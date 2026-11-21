// The app itself: tray icon, floating can, drink picker, hotkeys, and pasting the drink into the chat app.
using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace SecondWind
{
    public sealed class TrayApp : ApplicationContext
    {
        const string Bolt = "⚡", StarOn = "★", StarOff = "☆";
        const string StartupTaskId = "SecondWindStartup";

        static readonly Color ColBg = Color.FromArgb(20, 11, 38);
        static readonly Color ColCard = Color.FromArgb(31, 19, 56);
        static readonly Color ColHover = Color.FromArgb(46, 16, 101);
        static readonly Color ColText = Color.FromArgb(245, 243, 255);
        static readonly Color ColMuted = Color.FromArgb(196, 181, 253);
        static readonly Color ColGold = Color.FromArgb(251, 191, 36);
        static readonly string[] IgnoreClasses = {
            "Shell_TrayWnd", "Shell_SecondaryTrayWnd", "NotifyIconOverflowWindow", "TopLevelWindowForOverflowXamlIsland",
            "Windows.UI.Core.CoreWindow", "Progman", "WorkerW", "XamlExplorerHostIslandWindow" };

        readonly Settings state = Settings.Load();
        readonly bool firstRun;
        readonly float scale = 1f;
        readonly uint myPid = (uint)Environment.ProcessId;
        readonly Dictionary<string, Image> images = new Dictionary<string, Image>();
        readonly Random rng = new Random();
        readonly Font fontUi, fontSmall, fontTitle;
        readonly ToolTip tips = new ToolTip();
        readonly Icon appIcon;

        readonly NotifyIcon tray = new NotifyIcon();
        readonly ContextMenuStrip trayMenu = new ContextMenuStrip();
        readonly Form picker = new Form();
        readonly Label header = new Label(), hint = new Label();
        readonly FlowLayoutPanel grid = new FlowLayoutPanel(), bottom = new FlowLayoutPanel();
        readonly NoActivateForm floatCan = new NoActivateForm();
        readonly int floatSize;
        readonly Hotkeys hotkeys = new Hotkeys();
        readonly Timer watch = new Timer { Interval = 300 };

        IntPtr target = IntPtr.Zero;
        bool menuOpen, busy;
        Brand viewBrand;            // null = brand list
        TextBox customBox;
        Point dragStart, dragOrigin;
        bool dragging, dragMoved;
        Windows.ApplicationModel.StartupTask startup;   // null when not running as a Store app

        public TrayApp(bool firstRun)
        {
            this.firstRun = firstRun;
            using (var g = Graphics.FromHwnd(IntPtr.Zero)) scale = g.DpiX / 96f;
            fontUi = new Font("Segoe UI", 9f);
            fontSmall = new Font("Segoe UI", 8f);
            fontTitle = new Font("Segoe UI Semibold", 12f);
            try { appIcon = Icon.ExtractAssociatedIcon(Application.ExecutablePath); } catch { appIcon = SystemIcons.Application; }
            floatSize = Px(58);

            BuildPicker();
            BuildFloat();

            tray.Icon = appIcon;
            tray.Text = "Second Wind (Ctrl+Alt+D)";
            tray.ContextMenuStrip = trayMenu;
            tray.MouseUp += (s, e) => { if (e.Button == MouseButtons.Left) OpenPicker(); };
            tray.Visible = true;

            watch.Tick += (s, e) => RememberForeground();
            watch.Start();

            bool okPick = hotkeys.Add(1, Keys.D), okUsual = hotkeys.Add(2, Keys.U);
            hotkeys.Pressed += id =>
            {
                if (id == 1) OpenPicker();
                else if (id == 2) { RememberForeground(); var u = state.Usual(); _ = GiveDrink(u.Brand, u.Flavor); }
            };

            UpdateTrayMenu();
            UpdateFloat();
            _ = LoadStartupTask();

            var msg = "Drag the floating can anywhere. Click it (or press Ctrl+Alt+D) to pick a drink. Ctrl+Alt+U gives your usual.";
            if (!(okPick && okUsual)) msg = "Running in your tray, but another app already uses Ctrl+Alt+D or Ctrl+Alt+U. Click the can instead.";
            tray.ShowBalloonTip(5000, Bolt + " Second Wind is on", msg, ToolTipIcon.Info);
            if (firstRun) OpenPicker(centered: true);
        }

        public void SaveNow() { state.Save(); }

        // Used by the build to make Store screenshots: draws the picker and the floating can to PNG files.
        public void Snapshots(string dir)
        {
            Directory.CreateDirectory(dir);
            state.Favorites.Clear();
            foreach (var (b, f) in new[] { ("redbull", "Original"), ("monster", "Zero Ultra"), ("celsius", "Sparkling Orange"), ("ghost", "Sour Patch Kids Redberry") })
                if (Catalog.ById.ContainsKey(b)) state.Favorites.Add(new Drink(b, f));
            state.Total = 42;
            void Shot(Control c, string name)
            {
                Application.DoEvents();
                using (var bmp = new Bitmap(c.Width, c.Height))
                {
                    c.DrawToBitmap(bmp, new Rectangle(0, 0, c.Width, c.Height));
                    bmp.Save(Path.Combine(dir, name), System.Drawing.Imaging.ImageFormat.Png);
                }
            }
            OpenPicker(centered: true);
            Shot(picker, "picker-brands.png");
            ShowFlavors(Catalog.Get("redbull"));
            Shot(picker, "picker-flavors.png");
            picker.Hide();
            state.Last = state.Favorites[0];
            floatCan.Invalidate();
            Shot(floatCan, "float-can.png");
            UpdateTrayMenu();
            trayMenu.Show(new Point(200, 200));
            Shot(trayMenu, "tray-menu.png");
            trayMenu.Close();
        }

        int Px(double n) { return (int)Math.Round(n * scale); }

        protected override void Dispose(bool disposing)
        {
            if (disposing)
            {
                watch.Stop();
                hotkeys.Dispose();
                tray.Visible = false;
                tray.Dispose();
            }
            base.Dispose(disposing);
        }

        // ------------------------------------------------------------ pictures
        Image CanImage(string brandId, string slug)
        {
            var rel = string.IsNullOrEmpty(slug) ? Path.Combine("cans", brandId + ".png") : Path.Combine("cans", brandId, slug + ".png");
            Image img;
            if (images.TryGetValue(rel, out img)) return img;
            var path = Path.Combine(Catalog.AssetDir, rel);
            if (!File.Exists(path)) path = Path.Combine(Catalog.AssetDir, "cans", brandId + ".png");
            if (!File.Exists(path)) path = Path.Combine(Catalog.AssetDir, "cans", "mystery.png");
            int h = Px(64), w = h * 120 / 220;
            var bmp = new Bitmap(w, h);
            try
            {
                using (var src = Image.FromFile(path))
                using (var gr = Graphics.FromImage(bmp))
                {
                    gr.InterpolationMode = InterpolationMode.HighQualityBicubic;
                    gr.DrawImage(src, 0, 0, w, h);
                }
            }
            catch { }
            images[rel] = bmp;
            return bmp;
        }

        // ------------------------------------------------------------ which window gets the drink
        void RememberForeground()
        {
            var h = Native.GetForegroundWindow();
            if (h == IntPtr.Zero || Native.PidOf(h) == myPid) return;
            if (IgnoreClasses.Contains(Native.ClassOf(h))) return;
            target = h;
        }

        static async Task WaitKeysUp()
        {
            // Ctrl/Alt/Shift/Win still held from the hotkey would turn Ctrl+V into something else.
            var deadline = DateTime.Now.AddSeconds(2);
            while (DateTime.Now < deadline)
            {
                if (!new[] { 0x10, 0x11, 0x12, 0x5B, 0x5C }.Any(Native.KeyDown)) return;
                await Task.Delay(30);
            }
        }

        static void SetClipboard(string text)
        {
            for (int i = 0; i < 5; i++)
            {
                try { Clipboard.SetText(text); return; } catch { System.Threading.Thread.Sleep(60); }
            }
        }

        async Task GiveDrink(string brandId, string flavor)
        {
            if (busy) return;
            busy = true;
            try
            {
                var b = Catalog.Get(brandId);
                var f = b.Find(flavor);
                if (f != null) flavor = f.Name;
                state.Total++;
                state.Last = new Drink(b.Id, flavor);
                state.Save();
                var text = DrinkMessage.Build(b, flavor, f != null, state.Total);
                picker.Hide();

                string old = null;
                try { if (Clipboard.ContainsText()) old = Clipboard.GetText(); } catch { }
                SetClipboard(text);

                var t = target;
                if (t == IntPtr.Zero || !Native.IsWindow(t))
                {
                    tray.ShowBalloonTip(4000, "Second Wind", "Copied the drink. Click into your chat box and press Ctrl+V.", ToolTipIcon.Info);
                    return;
                }
                if (Native.IsIconic(t)) Native.ShowWindow(t, 9);
                Native.SetForegroundWindow(t);
                await WaitKeysUp();
                await Task.Delay(250);
                SendKeys.SendWait("^v");
                if (state.AutoSend) { await Task.Delay(300); SendKeys.SendWait("{ENTER}"); }
                await Task.Delay(700);
                if (old != null) SetClipboard(old);
            }
            finally
            {
                busy = false;
                UpdateTrayMenu();
                floatCan.Invalidate();
            }
        }

        // ------------------------------------------------------------ picker window
        void BuildPicker()
        {
            picker.Text = "Second Wind";
            picker.FormBorderStyle = FormBorderStyle.FixedToolWindow;
            picker.StartPosition = FormStartPosition.Manual;
            picker.TopMost = true;
            picker.ShowInTaskbar = false;
            picker.KeyPreview = true;
            picker.BackColor = ColBg;
            picker.ForeColor = ColText;
            picker.Font = fontUi;
            picker.Icon = appIcon;
            picker.ClientSize = new Size(Px(470), Px(560));
            picker.KeyDown += (s, e) => { if (e.KeyCode == Keys.Escape) picker.Hide(); };
            picker.Deactivate += (s, e) => { if (!menuOpen) picker.Hide(); };
            picker.FormClosing += (s, e) => { if (e.CloseReason == CloseReason.UserClosing) { e.Cancel = true; picker.Hide(); } };

            header.Font = fontTitle;
            header.ForeColor = ColText;
            header.Dock = DockStyle.Top;
            header.Height = Px(34);
            header.Padding = new Padding(Px(10), Px(6), 0, 0);

            hint.ForeColor = ColMuted;
            hint.Font = fontSmall;
            hint.Dock = DockStyle.Top;
            hint.Height = Px(20);
            hint.Padding = new Padding(Px(12), 0, 0, 0);

            grid.Dock = DockStyle.Fill;
            grid.AutoScroll = true;
            grid.Padding = new Padding(Px(6));
            grid.BackColor = ColBg;

            bottom.Dock = DockStyle.Bottom;
            bottom.Height = Px(74);
            bottom.Padding = new Padding(Px(8), Px(6), Px(8), 0);
            bottom.BackColor = ColBg;

            picker.Controls.Add(grid);
            picker.Controls.Add(bottom);
            picker.Controls.Add(hint);
            picker.Controls.Add(header);
        }

        Button FlatButton(string text, Color back, Color fore)
        {
            var b = new Button
            {
                Text = text,
                FlatStyle = FlatStyle.Flat,
                BackColor = back,
                ForeColor = fore,
                AutoSize = true,
                Height = Px(30),
                Padding = new Padding(Px(6), 0, Px(6), 0),
                Cursor = Cursors.Hand,
            };
            b.FlatAppearance.BorderSize = 0;
            return b;
        }

        void SectionLabel(string text)
        {
            var lab = new Label { Text = text, ForeColor = ColGold, Font = fontSmall, AutoSize = false, Width = Px(430), Height = Px(18) };
            grid.Controls.Add(lab);
            grid.SetFlowBreak(lab, true);
        }

        // brand tile opens its flavors; drink tile hands it over.
        Button CanTile(Brand b, string slug, string label, string flavor, bool usual)
        {
            bool isDrink = flavor != null;
            var tile = new Button
            {
                FlatStyle = FlatStyle.Flat,
                BackColor = ColCard,
                ForeColor = ColText,
                Font = fontSmall,
                Size = new Size(Px(100), Px(108)),
                Margin = new Padding(Px(3)),
                Image = CanImage(b.Id, slug),
                ImageAlign = ContentAlignment.TopCenter,
                TextAlign = ContentAlignment.BottomCenter,
                TextImageRelation = TextImageRelation.ImageAboveText,
                Cursor = Cursors.Hand,
            };
            tile.FlatAppearance.BorderSize = 1;
            tile.FlatAppearance.BorderColor = usual ? ColGold : ColCard;
            tile.FlatAppearance.MouseOverBackColor = ColHover;
            var star = isDrink && state.IsFav(b.Id, flavor) ? StarOn + " " : "";
            tile.Text = star + (label.Length > 26 ? label.Substring(0, 25) + "..." : label);
            tips.SetToolTip(tile, isDrink ? label + "\nClick to hand it over. Right-click to star it." : b.Vibe);
            tile.MouseUp += (s, e) =>
            {
                if (e.Button == MouseButtons.Right && isDrink) { ShowTileMenu(tile, b.Id, flavor, e.Location); return; }
                if (e.Button != MouseButtons.Left) return;
                if (isDrink) _ = GiveDrink(b.Id, flavor); else ShowFlavors(b);
            };
            return tile;
        }

        void ShowTileMenu(Control tile, string brandId, string flavor, Point where)
        {
            var m = new ContextMenuStrip();
            bool isFav = state.IsFav(brandId, flavor);
            m.Items.Add(isFav ? StarOff + " Remove from favorites" : StarOn + " Add to favorites", null,
                (s, e) => { state.ToggleFav(brandId, flavor); UpdateTrayMenu(); RefreshPicker(); });
            m.Items.Add("Make it my usual (Ctrl+Alt+U)", null,
                (s, e) => { state.MakeUsual(brandId, flavor); UpdateTrayMenu(); RefreshPicker(); });
            m.Opening += (s, e) => menuOpen = true;
            m.Closed += (s, e) => { menuOpen = false; if (!picker.ContainsFocus) picker.Activate(); };
            m.Show(tile, where);
        }

        void ShowBrands()
        {
            viewBrand = null;
            grid.SuspendLayout();
            ClearGrid();
            header.Text = Bolt + " Second Wind";
            hint.Text = "Pick a brand. Right-click a flavor to star it. Ctrl+Alt+U gives your usual.";
            if (state.Favorites.Count > 0)
            {
                SectionLabel(StarOn + " YOUR FAVORITES  (gold = your usual)");
                for (int i = 0; i < state.Favorites.Count; i++)
                {
                    var fav = state.Favorites[i];
                    if (!Catalog.ById.ContainsKey(fav.Brand)) continue;
                    var b = Catalog.ById[fav.Brand];
                    var f = b.Find(fav.Flavor);
                    grid.Controls.Add(CanTile(b, f?.Slug, b.Name + " " + fav.Flavor, fav.Flavor, i == 0));
                }
                if (grid.Controls.Count > 0) grid.SetFlowBreak(grid.Controls[grid.Controls.Count - 1], true);
            }
            SectionLabel("ALL BRANDS");
            foreach (var b in Catalog.Brands) grid.Controls.Add(CanTile(b, null, b.Name, null, false));
            grid.ResumeLayout();
            BuildBottom(null);
        }

        void ShowFlavors(Brand b)
        {
            viewBrand = b;
            grid.SuspendLayout();
            ClearGrid();
            header.Text = b.Name + "  (" + b.Size + ")";
            hint.Text = "Click a can to hand it over. Right-click to star it or make it your usual.";
            var usual = state.Favorites.Count > 0 ? state.Favorites[0] : null;
            foreach (var f in b.Flavors)
                grid.Controls.Add(CanTile(b, f.Slug, f.Name, f.Name, usual != null && usual.Same(b.Id, f.Name)));
            grid.ResumeLayout();
            BuildBottom(b);
        }

        void ClearGrid()
        {
            var old = grid.Controls.Cast<Control>().ToList();
            grid.Controls.Clear();
            foreach (var c in old) c.Dispose();   // the can pictures are cached, Button.Dispose leaves them alone
        }

        void RefreshPicker() { if (viewBrand != null) ShowFlavors(viewBrand); else ShowBrands(); }

        void BuildBottom(Brand b)
        {
            var old = bottom.Controls.Cast<Control>().ToList();
            bottom.Controls.Clear();
            foreach (var c in old) c.Dispose();
            if (b != null)
            {
                var back = FlatButton("< Back", ColHover, ColText);
                back.Click += (s, e) => ShowBrands();
                bottom.Controls.Add(back);
                customBox = new TextBox
                {
                    Width = Px(170),
                    MaxLength = 60,
                    BackColor = ColCard,
                    ForeColor = ColText,
                    BorderStyle = BorderStyle.FixedSingle,
                    PlaceholderText = "Make up a flavor",
                    Margin = new Padding(Px(3), Px(6), Px(3), Px(3)),
                };
                bottom.Controls.Add(customBox);
                var give = FlatButton("Give it", ColGold, ColBg);
                give.Click += (s, e) => GiveCustom();
                bottom.Controls.Add(give);
                var save = FlatButton(StarOn + " Save", ColHover, ColText);
                tips.SetToolTip(save, "Star your made-up flavor");
                save.Click += (s, e) =>
                {
                    var v = customBox.Text.Trim();
                    if (v.Length > 0 && !state.IsFav(b.Id, v)) { state.ToggleFav(b.Id, v); customBox.Text = ""; UpdateTrayMenu(); }
                };
                bottom.Controls.Add(save);
                customBox.KeyDown += (s, e) => { if (e.KeyCode == Keys.Enter) { e.SuppressKeyPress = true; GiveCustom(); } };
            }
            else
            {
                var u = state.Usual();
                var usualBtn = FlatButton(state.Favorites.Count > 0 ? Bolt + " My usual" : Bolt + " Quick can", ColGold, ColBg);
                tips.SetToolTip(usualBtn, Catalog.Get(u.Brand).Name + " " + u.Flavor);
                usualBtn.Click += (s, e) => { var x = state.Usual(); _ = GiveDrink(x.Brand, x.Flavor); };
                bottom.Controls.Add(usualBtn);
                var rnd = FlatButton("Surprise me", ColHover, ColText);
                rnd.Click += (s, e) =>
                {
                    var rb = Catalog.Brands[rng.Next(Catalog.Brands.Count)];
                    _ = GiveDrink(rb.Id, rb.Flavors[rng.Next(rb.Flavors.Count)].Name);
                };
                bottom.Controls.Add(rnd);
            }
            bottom.SetFlowBreak(bottom.Controls[bottom.Controls.Count - 1], true);
            var auto = new CheckBox { Text = "Send right away", ForeColor = ColMuted, AutoSize = true, Checked = state.AutoSend };
            auto.CheckedChanged += (s, e) => { state.AutoSend = auto.Checked; state.Save(); UpdateTrayMenu(); };
            bottom.Controls.Add(auto);
            bottom.Controls.Add(new Label
            {
                Text = "Lifetime: " + state.Total + (state.Total == 1 ? " can" : " cans"),
                ForeColor = ColMuted,
                AutoSize = true,
                Margin = new Padding(Px(12), Px(4), 0, 0),
            });
        }

        void GiveCustom()
        {
            var v = customBox?.Text.Trim() ?? "";
            if (v.Length > 0 && viewBrand != null) _ = GiveDrink(viewBrand.Id, v);
            else customBox?.Focus();
        }

        public void OpenPicker(bool centered = false)
        {
            RememberForeground();
            ShowBrands();
            Point pt = Cursor.Position;
            var wa = Screen.FromPoint(pt).WorkingArea;
            int x, y;
            if (centered)
            {
                wa = Screen.PrimaryScreen.WorkingArea;
                x = wa.Left + (wa.Width - picker.Width) / 2;
                y = wa.Top + (wa.Height - picker.Height) / 2;
            }
            else
            {
                x = Math.Min(Math.Max(wa.Left, pt.X - picker.Width / 2), wa.Right - picker.Width);
                y = Math.Min(Math.Max(wa.Top, pt.Y - picker.Height - Px(20)), wa.Bottom - picker.Height);
            }
            picker.Location = new Point(x, y);
            picker.Show();
            picker.Activate();
            Native.SetForegroundWindow(picker.Handle);
        }

        // ------------------------------------------------------------ tray menu
        void UpdateTrayMenu()
        {
            foreach (var it in trayMenu.Items.Cast<ToolStripItem>().ToList()) it.Dispose();
            trayMenu.Items.Clear();
            var u = state.Usual();
            var usual = trayMenu.Items.Add(Bolt + " Give my usual: " + Catalog.Get(u.Brand).Name + " " + u.Flavor + "   Ctrl+Alt+U", null,
                (s, e) => { var x = state.Usual(); _ = GiveDrink(x.Brand, x.Flavor); });
            usual.Font = new Font(trayMenu.Font, FontStyle.Bold);
            foreach (var fav in state.Favorites.Skip(1).ToList())
            {
                if (!Catalog.ById.ContainsKey(fav.Brand)) continue;
                var d = fav;
                trayMenu.Items.Add(StarOn + " " + Catalog.ById[d.Brand].Name + " " + d.Flavor, null, (s, e) => _ = GiveDrink(d.Brand, d.Flavor));
            }
            trayMenu.Items.Add("Pick a drink...   Ctrl+Alt+D", null, (s, e) => OpenPicker());
            trayMenu.Items.Add(new ToolStripSeparator());
            AddCheck("Send right away", state.AutoSend, () => { state.AutoSend = !state.AutoSend; state.Save(); UpdateTrayMenu(); });
            AddCheck("Show floating can", state.ShowFloat, () => { state.ShowFloat = !state.ShowFloat; state.Save(); UpdateFloat(); UpdateTrayMenu(); });
            if (startup != null)
            {
                bool on = startup.State == Windows.ApplicationModel.StartupTaskState.Enabled
                       || startup.State == Windows.ApplicationModel.StartupTaskState.EnabledByPolicy;
                AddCheck("Start with Windows", on, () => _ = ToggleStartup());
            }
            var c = trayMenu.Items.Add("Lifetime: " + state.Total + " cans  (v" + Catalog.Version + ")");
            c.Enabled = false;
            trayMenu.Items.Add(new ToolStripSeparator());
            trayMenu.Items.Add("Quit Second Wind", null, (s, e) => ExitThread());
        }

        void AddCheck(string text, bool on, Action click)
        {
            var i = new ToolStripMenuItem(text) { Checked = on };
            i.Click += (s, e) => click();
            trayMenu.Items.Add(i);
        }

        // ------------------------------------------------------------ start with Windows (Store "startup task")
        async Task LoadStartupTask()
        {
            try { startup = await Windows.ApplicationModel.StartupTask.GetAsync(StartupTaskId); }
            catch { startup = null; }   // not installed as a Store app
            UpdateTrayMenu();
        }

        async Task ToggleStartup()
        {
            if (startup == null) return;
            var s = startup.State;
            if (s == Windows.ApplicationModel.StartupTaskState.Enabled) startup.Disable();
            else if (s == Windows.ApplicationModel.StartupTaskState.Disabled)
            {
                var r = await startup.RequestEnableAsync();
                if (r == Windows.ApplicationModel.StartupTaskState.DisabledByUser) TellStartupBlocked();
            }
            else if (s == Windows.ApplicationModel.StartupTaskState.DisabledByUser) TellStartupBlocked();
            UpdateTrayMenu();
        }

        void TellStartupBlocked()
        {
            tray.ShowBalloonTip(6000, "Second Wind", "Windows has startup turned off for Second Wind. Turn it on in Settings > Apps > Startup.", ToolTipIcon.Info);
        }

        // ------------------------------------------------------------ floating can (drag it anywhere)
        void BuildFloat()
        {
            floatCan.FormBorderStyle = FormBorderStyle.None;
            floatCan.StartPosition = FormStartPosition.Manual;
            floatCan.ShowInTaskbar = false;
            floatCan.TopMost = true;
            floatCan.BackColor = Color.FromArgb(28, 16, 51);
            floatCan.Size = new Size(floatSize, floatSize);
            floatCan.Cursor = Cursors.Hand;
            var circle = new GraphicsPath();
            circle.AddEllipse(0, 0, floatSize, floatSize);
            floatCan.Region = new Region(circle);
            tips.SetToolTip(floatCan, "Second Wind\nClick: pick a drink   Drag: move me   Right-click: menu");
            floatCan.Paint += (s, e) =>
            {
                var gr = e.Graphics;
                gr.SmoothingMode = SmoothingMode.AntiAlias;
                gr.InterpolationMode = InterpolationMode.HighQualityBicubic;
                float o = Px(1.5);
                using (var pen = new Pen(ColGold, Px(3))) gr.DrawEllipse(pen, o, o, floatSize - 2 * o - 1, floatSize - 2 * o - 1);
                var u = state.Last ?? state.Usual();
                var b = Catalog.Get(u.Brand);
                var f = b.Find(u.Flavor);
                var img = CanImage(b.Id, f?.Slug);
                int h = (int)(floatSize * 0.72), w = h * 120 / 220;
                gr.DrawImage(img, (floatSize - w) / 2, (floatSize - h) / 2, w, h);
            };
            floatCan.MouseDown += (s, e) =>
            {
                if (e.Button != MouseButtons.Left) return;
                dragging = true; dragMoved = false;
                dragStart = Cursor.Position; dragOrigin = floatCan.Location;
            };
            floatCan.MouseMove += (s, e) =>
            {
                if (!dragging) return;
                var p = Cursor.Position;
                int dx = p.X - dragStart.X, dy = p.Y - dragStart.Y;
                if (!dragMoved && Math.Abs(dx) + Math.Abs(dy) < Px(5)) return;
                dragMoved = true;
                floatCan.Location = new Point(dragOrigin.X + dx, dragOrigin.Y + dy);
            };
            floatCan.MouseUp += (s, e) =>
            {
                if (e.Button == MouseButtons.Right) { trayMenu.Show(Cursor.Position); return; }
                if (!dragging) return;
                dragging = false;
                if (dragMoved) { state.FloatX = floatCan.Left; state.FloatY = floatCan.Top; state.Save(); }
                else OpenPicker();
            };
        }

        void UpdateFloat()
        {
            if (!state.ShowFloat) { floatCan.Hide(); return; }
            int x = state.FloatX, y = state.FloatY;
            bool onScreen = Screen.AllScreens.Any(sc => sc.WorkingArea.Contains(new Point(x + 10, y + 10)));
            if (!onScreen)
            {
                var wa = Screen.PrimaryScreen.WorkingArea;
                x = wa.Right - floatSize - Px(24);
                y = wa.Bottom - floatSize - Px(120);
            }
            floatCan.Location = new Point(x, y);
            if (!floatCan.Visible) floatCan.Show();
            floatCan.Invalidate();
        }
    }
}
