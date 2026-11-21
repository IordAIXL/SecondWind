// Second Wind for Windows: hand your AI a (pretend) energy drink from any chat app.
using System;
using System.IO;
using System.Threading;
using System.Windows.Forms;

namespace SecondWind
{
    static class Program
    {
        const string MutexName = @"Local\SecondWindStoreApp";
        const string OpenEventName = @"Local\SecondWindStoreApp.Open";

        [STAThread]
        static int Main(string[] args)
        {
            if (args.Length > 0 && args[0] == "--selftest") return SelfTest(args.Length > 1 ? args[1] : "selftest.txt");
            using var mutex = new Mutex(true, MutexName, out bool createdNew);
            using var openEvent = new EventWaitHandle(false, EventResetMode.AutoReset, OpenEventName);
            if (!createdNew)
            {
                // Already running (in the tray): opening the app again shows the drink picker.
                openEvent.Set();
                return 0;
            }

            Application.SetHighDpiMode(HighDpiMode.SystemAware);
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);

            try { Catalog.Load(); }
            catch (Exception e)
            {
                MessageBox.Show("Second Wind couldn't load its drinks: " + e.Message + "\nTry reinstalling it from the Microsoft Store.", "Second Wind");
                return 1;
            }

            bool firstRun = !File.Exists(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "SecondWind", "settings.json"));
            var app = new TrayApp(firstRun);
            if (firstRun) app.SaveNow();

            // Wait for "open again" signals from a second launch.
            var ui = SynchronizationContext.Current ?? new WindowsFormsSynchronizationContext();
            var waiter = new Thread(() =>
            {
                while (openEvent.WaitOne()) ui.Post(_ => app.OpenPicker(), null);
            }) { IsBackground = true, Name = "open-signal" };
            waiter.Start();

            Application.Run(app);
            return 0;
        }

        // Used by the build: loads the drinks, builds every message, opens the app for a moment, then quits.
        static int SelfTest(string report)
        {
            var log = new System.Text.StringBuilder();
            int code = 0;
            try
            {
                Application.SetHighDpiMode(HighDpiMode.SystemAware);
                Application.EnableVisualStyles();
                Catalog.Load();
                foreach (var b in Catalog.Brands)
                    foreach (var f in b.Flavors)
                        if (DrinkMessage.Build(b, f.Name, true, 1).Length < 200) throw new Exception("short message for " + b.Id);
                log.AppendLine("brands: " + Catalog.Brands.Count + ", version " + Catalog.Version);
                log.AppendLine(DrinkMessage.Build(Catalog.Get(null), "Original", true, 5));
                var app = new TrayApp(false);
                app.OpenPicker();
                var t = new System.Windows.Forms.Timer { Interval = 3000 };
                t.Tick += (s, e) => { t.Stop(); app.ExitThread(); };
                t.Start();
                Application.Run(app);
                log.AppendLine("UI opened and closed fine.");
            }
            catch (Exception e) { log.AppendLine("FAILED: " + e); code = 1; }
            File.WriteAllText(report, log.ToString());
            return code;
        }
    }
}
