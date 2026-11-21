# Second Wind for desktop apps (Windows).
# A tray app: press Ctrl+Alt+D in any chat app (ChatGPT, Claude, Copilot, ...) to pick a drink,
# or Ctrl+Alt+U to hand over your usual instantly. The drink message gets pasted into the chat box.
# Start it with "Start Second Wind.bat". Settings live in %APPDATA%\SecondWind\settings.json.

$ErrorActionPreference = 'Stop'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path

# ---------------------------------------------------------------- one copy only
$createdNew = $false
$script:Mutex = New-Object System.Threading.Mutex($true, 'Local\SecondWindTrayApp', [ref]$createdNew)
if (-not $createdNew) { exit 0 }

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

Add-Type -ReferencedAssemblies System.Windows.Forms -TypeDefinition @"
using System;
using System.Text;
using System.Runtime.InteropServices;
using System.Windows.Forms;

public static class SWNative {
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr h);
    [DllImport("user32.dll")] public static extern bool IsWindow(IntPtr h);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int cmd);
    [DllImport("user32.dll")] public static extern short GetAsyncKeyState(int vk);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern int GetClassName(IntPtr h, StringBuilder s, int n);
    [DllImport("user32.dll")] public static extern bool RegisterHotKey(IntPtr h, int id, uint mods, uint vk);
    [DllImport("user32.dll")] public static extern bool UnregisterHotKey(IntPtr h, int id);
    [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();

    public static uint PidOf(IntPtr h) { uint pid; GetWindowThreadProcessId(h, out pid); return pid; }
    public static string ClassOf(IntPtr h) { var sb = new StringBuilder(256); GetClassName(h, sb, 256); return sb.ToString(); }
    public static bool KeyDown(int vk) { return (GetAsyncKeyState(vk) & 0x8000) != 0; }
}

// A small always-on-top window that never steals focus from the chat app.
public class SWFloat : Form {
    protected override bool ShowWithoutActivation { get { return true; } }
    protected override CreateParams CreateParams {
        get {
            var cp = base.CreateParams;
            cp.ExStyle |= 0x08000000 | 0x00000080 | 0x00000008; // NOACTIVATE | TOOLWINDOW | TOPMOST
            return cp;
        }
    }
    public SWFloat() { SetStyle(ControlStyles.OptimizedDoubleBuffer | ControlStyles.AllPaintingInWmPaint | ControlStyles.UserPaint, true); }
}

// Invisible window that receives global hotkey presses.
public class SWHotkeys : NativeWindow {
    public event EventHandler Pressed;
    public int LastId;
    public SWHotkeys() { CreateHandle(new CreateParams()); }
    protected override void WndProc(ref Message m) {
        if (m.Msg == 0x0312) { LastId = m.WParam.ToInt32(); var h = Pressed; if (h != null) h(this, EventArgs.Empty); }
        base.WndProc(ref m);
    }
}
"@

[void][SWNative]::SetProcessDPIAware()
[System.Windows.Forms.Application]::EnableVisualStyles()

# ---------------------------------------------------------------- data + settings
$Data = Get-Content -Raw -Encoding UTF8 (Join-Path $Here 'data.json') | ConvertFrom-Json
$Brands = @($Data.brands)
$BrandById = @{}
foreach ($b in $Brands) { $BrandById[$b.id] = $b }

$SettingsDir = Join-Path $env:APPDATA 'SecondWind'
$SettingsFile = Join-Path $SettingsDir 'settings.json'
$State = [ordered]@{ total = 0; autoSend = $false; favorites = @(); last = $null; showFloat = $true; floatX = -1; floatY = -1 }
if (Test-Path $SettingsFile) {
    try {
        $s = Get-Content -Raw -Encoding UTF8 $SettingsFile | ConvertFrom-Json
        if ($null -ne $s.total) { $State.total = [int]$s.total }
        if ($null -ne $s.autoSend) { $State.autoSend = [bool]$s.autoSend }
        if ($null -ne $s.favorites) { $State.favorites = @($s.favorites | ForEach-Object { [pscustomobject]@{ brand = [string]$_.brand; flavor = [string]$_.flavor } }) }
        if ($null -ne $s.showFloat) { $State.showFloat = [bool]$s.showFloat }
        if ($null -ne $s.floatX) { $State.floatX = [int]$s.floatX; $State.floatY = [int]$s.floatY }
        if ($null -ne $s.last) { $State.last = [pscustomobject]@{ brand = [string]$s.last.brand; flavor = [string]$s.last.flavor } }
    } catch { }
}
function Save-State {
    try {
        if (-not (Test-Path $SettingsDir)) { New-Item -ItemType Directory -Path $SettingsDir | Out-Null }
        $json = [pscustomobject]@{ total = $State.total; autoSend = $State.autoSend; favorites = @($State.favorites); last = $State.last; showFloat = $State.showFloat; floatX = $State.floatX; floatY = $State.floatY } | ConvertTo-Json -Depth 4
        [System.IO.File]::WriteAllText($SettingsFile, $json, (New-Object System.Text.UTF8Encoding($false)))
    } catch { }
}

# ---------------------------------------------------------------- looks
$Scale = 1.0
try { $g = [System.Drawing.Graphics]::FromHwnd([IntPtr]::Zero); $Scale = $g.DpiX / 96.0; $g.Dispose() } catch { }
function Px([double]$n) { [int][Math]::Round($n * $Scale) }

$ColBg = [System.Drawing.Color]::FromArgb(20, 11, 38)
$ColCard = [System.Drawing.Color]::FromArgb(31, 19, 56)
$ColHover = [System.Drawing.Color]::FromArgb(46, 16, 101)
$ColText = [System.Drawing.Color]::FromArgb(245, 243, 255)
$ColMuted = [System.Drawing.Color]::FromArgb(196, 181, 253)
$ColGold = [System.Drawing.Color]::FromArgb(251, 191, 36)
$FontUi = New-Object System.Drawing.Font('Segoe UI', 9)
$FontSmall = New-Object System.Drawing.Font('Segoe UI', 8)
$FontTitle = New-Object System.Drawing.Font('Segoe UI Semibold', 12)
$Bolt = [string][char]0x26A1
$StarOn = [string][char]0x2605
$StarOff = [string][char]0x2606

$ImageCache = @{}
function Get-CanImage([string]$brandId, [string]$slug) {
    $rel = if ($slug) { "cans\$brandId\$slug.png" } else { "cans\$brandId.png" }
    if ($ImageCache.ContainsKey($rel)) { return $ImageCache[$rel] }
    $path = Join-Path $Here $rel
    if (-not (Test-Path $path)) { $path = Join-Path $Here "cans\$brandId.png" }
    if (-not (Test-Path $path)) { $path = Join-Path $Here 'cans\mystery.png' }
    $h = Px 64; $w = [int]($h * 120 / 220)
    $bmp = New-Object System.Drawing.Bitmap($w, $h)
    $src = [System.Drawing.Image]::FromFile($path)
    $gr = [System.Drawing.Graphics]::FromImage($bmp)
    $gr.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $gr.DrawImage($src, 0, 0, $w, $h)
    $gr.Dispose(); $src.Dispose()
    $ImageCache[$rel] = $bmp
    return $bmp
}

# ---------------------------------------------------------------- favorites
function Find-Flavor($b, [string]$flavor) {
    foreach ($f in $b.flavors) { if ($f.name -ieq $flavor) { return $f } }
    return $null
}
function Test-Fav([string]$brandId, [string]$flavor) {
    foreach ($f in $State.favorites) { if ($f.brand -eq $brandId -and $f.flavor -ieq $flavor) { return $true } }
    return $false
}
function Toggle-Fav([string]$brandId, [string]$flavor) {
    if (Test-Fav $brandId $flavor) {
        $State.favorites = @($State.favorites | Where-Object { -not ($_.brand -eq $brandId -and $_.flavor -ieq $flavor) })
    } else {
        $State.favorites = @($State.favorites) + @([pscustomobject]@{ brand = $brandId; flavor = $flavor })
    }
    Save-State; Update-TrayMenu
}
function Set-Usual([string]$brandId, [string]$flavor) {
    $rest = @($State.favorites | Where-Object { -not ($_.brand -eq $brandId -and $_.flavor -ieq $flavor) })
    $State.favorites = @([pscustomobject]@{ brand = $brandId; flavor = $flavor }) + $rest
    Save-State; Update-TrayMenu
}
function Get-Usual {
    if ($State.favorites.Count -gt 0) { return $State.favorites[0] }
    if ($State.last) { return $State.last }
    $b = $BrandById[$Data.default]
    return [pscustomobject]@{ brand = $b.id; flavor = $b.flavors[0].name }
}

# ---------------------------------------------------------------- the message
function New-DrinkMessage($b, [string]$flavor, [bool]$known, [int]$n) {
    $l = New-Object System.Collections.Generic.List[string]
    $l.Add("$Bolt Second Wind: *slides you an ice-cold $($b.name) $flavor ($($b.size))*")
    if ($known) { $l.Add("Crack it open! Open with `"$($b.sip)`" and then one short line on how $flavor tastes.") }
    else { $l.Add("Crack it open! (Fun fact: I'm not sure $($b.name) even makes $flavor. React to that, then drink it anyway.) One short line on how it tastes.") }
    $pur = $b.purpose
    if ($pur -and $pur.mode) {
        $how = if ($pur.how) { ' Work style: ' + (@($pur.how) -join ' ') } else { '' }
        $l.Add("Mode: $($pur.mode). $($pur.for)$how")
    }
    $tail = '.'
    if ($n -eq 1) { $tail = '. First one!' } elseif (@(5, 10, 25, 50, 100) -contains $n) { $tail = '. Milestone!' }
    $l.Add("That's drink #$n I've handed you$tail")
    $l.Add('')
    $l.Add('Now get your second wind. Refocus on our real work and print this, short and honest:')
    $l.Add("$Bolt DIALED IN" + $(if ($pur -and $pur.mode) { " $([char]0x00B7) $($pur.mode)" } else { '' }))
    $l.Add('Goal: <what we are actually trying to do>')
    $l.Add('Done: <what is finished so far>')
    $l.Add('Left: <what is still open>')
    $l.Add('Dropping: <tangents we are parking, or nothing>')
    $l.Add('Next step: <the single next concrete action>')
    $l.Add('')
    $l.Add("Then do that next step right away: fewer words, no tangents. If there's no task yet, ask me one crisp question. (Pretend drink, just for fun.)")
    return ($l -join "`r`n")
}

# ---------------------------------------------------------------- which window gets the drink
$MyPid = [uint32][System.Diagnostics.Process]::GetCurrentProcess().Id
$script:Target = [IntPtr]::Zero
$IgnoreClasses = @('Shell_TrayWnd', 'Shell_SecondaryTrayWnd', 'NotifyIconOverflowWindow', 'TopLevelWindowForOverflowXamlIsland', 'Windows.UI.Core.CoreWindow', 'Progman', 'WorkerW', 'XamlExplorerHostIslandWindow')
function Remember-Foreground {
    $h = [SWNative]::GetForegroundWindow()
    if ($h -eq [IntPtr]::Zero) { return }
    if ([SWNative]::PidOf($h) -eq $MyPid) { return }
    if ($IgnoreClasses -contains [SWNative]::ClassOf($h)) { return }
    $script:Target = $h
}
$Watch = New-Object System.Windows.Forms.Timer
$Watch.Interval = 300
$Watch.Add_Tick({ Remember-Foreground })
$Watch.Start()

function Wait-KeysUp {
    # Ctrl/Alt/Shift/Win still held from the hotkey would turn Ctrl+V into something else.
    $deadline = [DateTime]::Now.AddSeconds(2)
    while ([DateTime]::Now -lt $deadline) {
        $held = $false
        foreach ($vk in 0x10, 0x11, 0x12, 0x5B, 0x5C) { if ([SWNative]::KeyDown($vk)) { $held = $true } }
        if (-not $held) { return }
        Start-Sleep -Milliseconds 30
        [System.Windows.Forms.Application]::DoEvents()
    }
}

function Give-Drink([string]$brandId, [string]$flavor) {
    $b = $BrandById[$brandId]
    if (-not $b) { $b = $BrandById[$Data.default] }
    $f = Find-Flavor $b $flavor
    if ($f) { $flavor = $f.name }
    $State.total = $State.total + 1
    $text = New-DrinkMessage $b $flavor ($null -ne $f) $State.total
    $Picker.Hide()

    $old = $null
    try { if ([System.Windows.Forms.Clipboard]::ContainsText()) { $old = [System.Windows.Forms.Clipboard]::GetText() } } catch { }
    try { [System.Windows.Forms.Clipboard]::SetText($text) } catch { Start-Sleep -Milliseconds 100; [System.Windows.Forms.Clipboard]::SetText($text) }

    $t = $script:Target
    if ($t -eq [IntPtr]::Zero -or -not [SWNative]::IsWindow($t)) {
        $Tray.ShowBalloonTip(4000, 'Second Wind', 'Copied the drink. Click into your chat box and press Ctrl+V.', [System.Windows.Forms.ToolTipIcon]::Info)
        $State.last = [pscustomobject]@{ brand = $b.id; flavor = $flavor }; Save-State; Update-TrayMenu
        return
    }
    if ([SWNative]::IsIconic($t)) { [void][SWNative]::ShowWindow($t, 9) }
    [void][SWNative]::SetForegroundWindow($t)
    Wait-KeysUp
    Start-Sleep -Milliseconds 250
    [System.Windows.Forms.SendKeys]::SendWait('^v')
    if ($State.autoSend) { Start-Sleep -Milliseconds 300; [System.Windows.Forms.SendKeys]::SendWait('{ENTER}') }
    Start-Sleep -Milliseconds 700
    try { if ($null -ne $old) { [System.Windows.Forms.Clipboard]::SetText($old) } } catch { }

    $State.last = [pscustomobject]@{ brand = $b.id; flavor = $flavor }
    Save-State; Update-TrayMenu; $Float.Invalidate()
}

# ---------------------------------------------------------------- the picker window
$Picker = New-Object System.Windows.Forms.Form
$Picker.Text = 'Second Wind'
$Picker.FormBorderStyle = 'FixedToolWindow'
$Picker.StartPosition = 'Manual'
$Picker.TopMost = $true
$Picker.ShowInTaskbar = $false
$Picker.KeyPreview = $true
$Picker.BackColor = $ColBg
$Picker.ForeColor = $ColText
$Picker.Font = $FontUi
$Picker.ClientSize = New-Object System.Drawing.Size((Px 470), (Px 560))
try { $Picker.Icon = New-Object System.Drawing.Icon (Join-Path $Here 'icon.ico') } catch { }
$Picker.Add_KeyDown({ if ($_.KeyCode -eq 'Escape') { $Picker.Hide() } })
$Picker.Add_Deactivate({ if (-not $script:MenuOpen) { $Picker.Hide() } })
$Picker.Add_FormClosing({ if ($_.CloseReason -eq 'UserClosing') { $_.Cancel = $true; $Picker.Hide() } })

$Header = New-Object System.Windows.Forms.Label
$Header.Font = $FontTitle
$Header.ForeColor = $ColText
$Header.AutoSize = $false
$Header.Dock = 'Top'
$Header.Height = Px 34
$Header.Padding = New-Object System.Windows.Forms.Padding((Px 10), (Px 6), 0, 0)

$Hint = New-Object System.Windows.Forms.Label
$Hint.ForeColor = $ColMuted
$Hint.Font = $FontSmall
$Hint.Dock = 'Top'
$Hint.Height = Px 20
$Hint.Padding = New-Object System.Windows.Forms.Padding((Px 12), 0, 0, 0)

$Grid = New-Object System.Windows.Forms.FlowLayoutPanel
$Grid.Dock = 'Fill'
$Grid.AutoScroll = $true
$Grid.Padding = New-Object System.Windows.Forms.Padding((Px 6))
$Grid.BackColor = $ColBg

$Bottom = New-Object System.Windows.Forms.FlowLayoutPanel
$Bottom.Dock = 'Bottom'
$Bottom.Height = Px 74
$Bottom.Padding = New-Object System.Windows.Forms.Padding((Px 8), (Px 6), (Px 8), 0)
$Bottom.BackColor = $ColBg

$Picker.Controls.Add($Grid)
$Picker.Controls.Add($Bottom)
$Picker.Controls.Add($Hint)
$Picker.Controls.Add($Header)

function New-FlatButton([string]$text, [System.Drawing.Color]$back, [System.Drawing.Color]$fore) {
    $btn = New-Object System.Windows.Forms.Button
    $btn.Text = $text
    $btn.FlatStyle = 'Flat'
    $btn.FlatAppearance.BorderSize = 0
    $btn.BackColor = $back
    $btn.ForeColor = $fore
    $btn.AutoSize = $true
    $btn.Height = Px 30
    $btn.Padding = New-Object System.Windows.Forms.Padding((Px 6), 0, (Px 6), 0)
    $btn.Cursor = [System.Windows.Forms.Cursors]::Hand
    return $btn
}

function New-SectionLabel([string]$text) {
    $lab = New-Object System.Windows.Forms.Label
    $lab.Text = $text
    $lab.ForeColor = $ColGold
    $lab.Font = $FontSmall
    $lab.AutoSize = $false
    $lab.Width = Px 430
    $lab.Height = Px 18
    $Grid.Controls.Add($lab)
    $Grid.SetFlowBreak($lab, $true)
}

# One can tile. $kind: 'brand' opens flavors; 'drink' gives it.
function New-CanTile([string]$brandId, [string]$slug, [string]$label, [string]$kind, [string]$flavor, [bool]$usual) {
    $tile = New-Object System.Windows.Forms.Button
    $tile.FlatStyle = 'Flat'
    $tile.FlatAppearance.BorderSize = 1
    $tile.FlatAppearance.BorderColor = $(if ($usual) { $ColGold } else { $ColCard })
    $tile.FlatAppearance.MouseOverBackColor = $ColHover
    $tile.BackColor = $ColCard
    $tile.ForeColor = $ColText
    $tile.Font = $FontSmall
    $tile.Size = New-Object System.Drawing.Size((Px 100), (Px 108))
    $tile.Margin = New-Object System.Windows.Forms.Padding((Px 3))
    $tile.Image = Get-CanImage $brandId $slug
    $tile.ImageAlign = 'TopCenter'
    $tile.TextAlign = 'BottomCenter'
    $tile.TextImageRelation = 'ImageAboveText'
    $tile.Cursor = [System.Windows.Forms.Cursors]::Hand
    $star = ''
    if ($kind -eq 'drink') { $star = $(if (Test-Fav $brandId $flavor) { "$StarOn " } else { '' }) }
    $tile.Text = $star + $(if ($label.Length -gt 26) { $label.Substring(0, 25) + '...' } else { $label })
    $tile.Tag = @{ brand = $brandId; flavor = $flavor; kind = $kind }
    $Tips.SetToolTip($tile, $(if ($kind -eq 'drink') { "$label`nClick to hand it over. Right-click to star it." } else { $BrandById[$brandId].vibe }))
    $tile.Add_MouseUp({
        param($src, $e)
        $t = $src.Tag
        if ($e.Button -eq 'Right' -and $t.kind -eq 'drink') { Show-TileMenu $src $t.brand $t.flavor $e.Location; return }
        if ($e.Button -ne 'Left') { return }
        if ($t.kind -eq 'brand') { Show-Flavors $BrandById[$t.brand] } else { Give-Drink $t.brand $t.flavor }
    })
    return $tile
}

$Tips = New-Object System.Windows.Forms.ToolTip
$script:MenuOpen = $false
function Show-TileMenu($tile, [string]$brandId, [string]$flavor, $where) {
    $m = New-Object System.Windows.Forms.ContextMenuStrip
    $isFav = Test-Fav $brandId $flavor
    $a = $m.Items.Add($(if ($isFav) { "$StarOff Remove from favorites" } else { "$StarOn Add to favorites" }))
    $a.Tag = @{ b = $brandId; f = $flavor }
    $a.Add_Click({ param($s) Toggle-Fav $s.Tag.b $s.Tag.f; Refresh-Picker })
    $u = $m.Items.Add('Make it my usual (Ctrl+Alt+U)')
    $u.Tag = @{ b = $brandId; f = $flavor }
    $u.Add_Click({ param($s) Set-Usual $s.Tag.b $s.Tag.f; Refresh-Picker })
    $m.Add_Opening({ $script:MenuOpen = $true })
    $m.Add_Closed({ $script:MenuOpen = $false; if (-not $Picker.ContainsFocus) { $Picker.Activate() } })
    $m.Show($tile, $where)
}

$script:View = 'brands'
$script:ViewBrand = $null

function Add-Favorites {
    if ($State.favorites.Count -eq 0) { return }
    New-SectionLabel "$StarOn YOUR FAVORITES  (gold = your usual)"
    $i = 0
    foreach ($fav in $State.favorites) {
        $b = $BrandById[$fav.brand]
        if (-not $b) { continue }
        $f = Find-Flavor $b $fav.flavor
        $slug = if ($f) { $f.slug } else { '' }
        $Grid.Controls.Add((New-CanTile $b.id $slug "$($b.name) $($fav.flavor)" 'drink' $fav.flavor ($i -eq 0)))
        $i++
    }
    $last = $Grid.Controls[$Grid.Controls.Count - 1]
    $Grid.SetFlowBreak($last, $true)
}

function Show-Brands {
    $script:View = 'brands'
    $Grid.SuspendLayout()
    $Grid.Controls.Clear()
    $Header.Text = "$Bolt Second Wind"
    $Hint.Text = 'Pick a brand. Right-click a flavor to star it. Ctrl+Alt+U gives your usual.'
    Add-Favorites
    New-SectionLabel 'ALL BRANDS'
    foreach ($b in $Brands) { $Grid.Controls.Add((New-CanTile $b.id '' $b.name 'brand' '' $false)) }
    $Grid.ResumeLayout()
    Build-Bottom $null
}

function Show-Flavors($b) {
    $script:View = 'flavors'
    $script:ViewBrand = $b
    $Grid.SuspendLayout()
    $Grid.Controls.Clear()
    $Header.Text = "$($b.name)  ($($b.size))"
    $Hint.Text = 'Click a can to hand it over. Right-click to star it or make it your usual.'
    $usual = Get-Usual
    foreach ($f in $b.flavors) {
        $isUsual = ($State.favorites.Count -gt 0 -and $usual.brand -eq $b.id -and $usual.flavor -ieq $f.name)
        $Grid.Controls.Add((New-CanTile $b.id $f.slug $f.name 'drink' $f.name $isUsual))
    }
    $Grid.ResumeLayout()
    Build-Bottom $b
}

function Refresh-Picker { if ($script:View -eq 'flavors' -and $script:ViewBrand) { Show-Flavors $script:ViewBrand } else { Show-Brands } }

function Build-Bottom($b) {
    $Bottom.Controls.Clear()
    if ($b) {
        $back = New-FlatButton '< Back' $ColHover $ColText
        $back.Add_Click({ Show-Brands })
        $Bottom.Controls.Add($back)
        $box = New-Object System.Windows.Forms.TextBox
        $box.Width = Px 170
        $box.MaxLength = 60
        $box.BackColor = $ColCard
        $box.ForeColor = $ColText
        $box.BorderStyle = 'FixedSingle'
        $box.Margin = New-Object System.Windows.Forms.Padding((Px 3), (Px 6), (Px 3), (Px 3))
        $Tips.SetToolTip($box, 'Make up a flavor')
        $script:CustomBox = $box
        $Bottom.Controls.Add($box)
        $give = New-FlatButton 'Give it' $ColGold $ColBg
        $give.Add_Click({ $v = $script:CustomBox.Text.Trim(); if ($v) { Give-Drink $script:ViewBrand.id $v } else { $script:CustomBox.Focus() } })
        $Bottom.Controls.Add($give)
        $save = New-FlatButton "$StarOn Save" $ColHover $ColText
        $Tips.SetToolTip($save, 'Star your made-up flavor')
        $save.Add_Click({ $v = $script:CustomBox.Text.Trim(); if ($v -and -not (Test-Fav $script:ViewBrand.id $v)) { Toggle-Fav $script:ViewBrand.id $v; $script:CustomBox.Text = '' } })
        $Bottom.Controls.Add($save)
        $box.Add_KeyDown({ if ($_.KeyCode -eq 'Enter') { $_.SuppressKeyPress = $true; $v = $script:CustomBox.Text.Trim(); if ($v) { Give-Drink $script:ViewBrand.id $v } } })
    } else {
        $u = Get-Usual
        $ub = $BrandById[$u.brand]
        $usualBtn = New-FlatButton $(if ($State.favorites.Count -gt 0) { "$Bolt My usual" } else { "$Bolt Quick can" }) $ColGold $ColBg
        $Tips.SetToolTip($usualBtn, "$($ub.name) $($u.flavor)")
        $usualBtn.Add_Click({ $x = Get-Usual; Give-Drink $x.brand $x.flavor })
        $Bottom.Controls.Add($usualBtn)
        $rnd = New-FlatButton 'Surprise me' $ColHover $ColText
        $rnd.Add_Click({ $rb = $Brands | Get-Random; Give-Drink $rb.id ($rb.flavors | Get-Random).name })
        $Bottom.Controls.Add($rnd)
    }
    $Bottom.SetFlowBreak($Bottom.Controls[$Bottom.Controls.Count - 1], $true)
    $auto = New-Object System.Windows.Forms.CheckBox
    $auto.Text = 'Send right away'
    $auto.ForeColor = $ColMuted
    $auto.AutoSize = $true
    $auto.Checked = $State.autoSend
    $auto.Add_CheckedChanged({ param($s) $State.autoSend = $s.Checked; Save-State; Update-TrayMenu })
    $Bottom.Controls.Add($auto)
    $count = New-Object System.Windows.Forms.Label
    $count.Text = "Lifetime: $($State.total) can$(if ($State.total -ne 1) { 's' })"
    $count.ForeColor = $ColMuted
    $count.AutoSize = $true
    $count.Margin = New-Object System.Windows.Forms.Padding((Px 12), (Px 4), 0, 0)
    $Bottom.Controls.Add($count)
}

function Open-Picker {
    Remember-Foreground
    Show-Brands
    $pt = [System.Windows.Forms.Cursor]::Position
    $wa = [System.Windows.Forms.Screen]::FromPoint($pt).WorkingArea
    $x = [Math]::Min([Math]::Max($wa.Left, $pt.X - [int]($Picker.Width / 2)), $wa.Right - $Picker.Width)
    $y = [Math]::Min([Math]::Max($wa.Top, $pt.Y - $Picker.Height - (Px 20)), $wa.Bottom - $Picker.Height)
    $Picker.Location = New-Object System.Drawing.Point($x, $y)
    $Picker.Show()
    $Picker.Activate()
    [void][SWNative]::SetForegroundWindow($Picker.Handle)
}

# ---------------------------------------------------------------- tray icon
$Tray = New-Object System.Windows.Forms.NotifyIcon
try { $Tray.Icon = New-Object System.Drawing.Icon (Join-Path $Here 'icon.ico') } catch { $Tray.Icon = [System.Drawing.SystemIcons]::Application }
$Tray.Text = 'Second Wind (Ctrl+Alt+D)'
$Tray.Visible = $true
$TrayMenu = New-Object System.Windows.Forms.ContextMenuStrip
$Tray.ContextMenuStrip = $TrayMenu
$Tray.Add_MouseUp({ param($s, $e) if ($e.Button -eq 'Left') { Open-Picker } })

$StartupLink = Join-Path ([Environment]::GetFolderPath('Startup')) 'Second Wind.lnk'
function Set-Startup([bool]$on) {
    if ($on) {
        $sh = New-Object -ComObject WScript.Shell
        $lnk = $sh.CreateShortcut($StartupLink)
        $lnk.TargetPath = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
        $lnk.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$(Join-Path $Here 'SecondWind.ps1')`""
        $lnk.WorkingDirectory = $Here
        $lnk.IconLocation = Join-Path $Here 'icon.ico'
        $lnk.WindowStyle = 7
        $lnk.Save()
    } elseif (Test-Path $StartupLink) { Remove-Item $StartupLink -Force }
}

function Update-TrayMenu {
    $TrayMenu.Items.Clear()
    $u = Get-Usual
    $ub = $BrandById[$u.brand]
    $i = $TrayMenu.Items.Add("$Bolt Give my usual: $($ub.name) $($u.flavor)   Ctrl+Alt+U")
    $i.Font = New-Object System.Drawing.Font($TrayMenu.Font, [System.Drawing.FontStyle]::Bold)
    $i.Add_Click({ $x = Get-Usual; Give-Drink $x.brand $x.flavor })
    if ($State.favorites.Count -gt 1) {
        foreach ($fav in @($State.favorites)[1..($State.favorites.Count - 1)]) {
            $fb = $BrandById[$fav.brand]
            if (-not $fb) { continue }
            $it = $TrayMenu.Items.Add("$StarOn $($fb.name) $($fav.flavor)")
            $it.Tag = @{ b = $fav.brand; f = $fav.flavor }
            $it.Add_Click({ param($s) Give-Drink $s.Tag.b $s.Tag.f })
        }
    }
    $p = $TrayMenu.Items.Add('Pick a drink...   Ctrl+Alt+D')
    $p.Add_Click({ Open-Picker })
    [void]$TrayMenu.Items.Add('-')
    $a = $TrayMenu.Items.Add('Send right away')
    $a.Checked = $State.autoSend
    $a.Add_Click({ $State.autoSend = -not $State.autoSend; Save-State; Update-TrayMenu })
    $fl = $TrayMenu.Items.Add('Show floating can')
    $fl.Checked = $State.showFloat
    $fl.Add_Click({ $State.showFloat = -not $State.showFloat; Save-State; Update-Float; Update-TrayMenu })
    $st = $TrayMenu.Items.Add('Start with Windows')
    $st.Checked = (Test-Path $StartupLink)
    $st.Add_Click({ Set-Startup (-not (Test-Path $StartupLink)); Update-TrayMenu })
    $c = $TrayMenu.Items.Add("Lifetime: $($State.total) cans  (v$($Data.version))")
    $c.Enabled = $false
    [void]$TrayMenu.Items.Add('-')
    $q = $TrayMenu.Items.Add('Quit Second Wind')
    $q.Add_Click({ [System.Windows.Forms.Application]::Exit() })
}

# ---------------------------------------------------------------- floating can (drag it anywhere)
$Float = New-Object SWFloat
$Float.FormBorderStyle = 'None'
$Float.StartPosition = 'Manual'
$Float.ShowInTaskbar = $false
$Float.TopMost = $true
$Float.BackColor = [System.Drawing.Color]::FromArgb(28, 16, 51)
$FloatSize = Px 58
$Float.Size = New-Object System.Drawing.Size($FloatSize, $FloatSize)
$Float.Cursor = [System.Windows.Forms.Cursors]::Hand
$circle = New-Object System.Drawing.Drawing2D.GraphicsPath
$circle.AddEllipse(0, 0, $FloatSize, $FloatSize)
$Float.Region = New-Object System.Drawing.Region($circle)
$Tips.SetToolTip($Float, "Second Wind`nClick: pick a drink   Drag: move me   Right-click: menu")
$Float.Add_Paint({
    param($s, $e)
    $gr = $e.Graphics
    $gr.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $gr.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $pen = New-Object System.Drawing.Pen($ColGold, [single](Px 3))
    $o = [single](Px 1.5)
    $gr.DrawEllipse($pen, $o, $o, [single]($FloatSize - 2 * $o - 1), [single]($FloatSize - 2 * $o - 1))
    $pen.Dispose()
    $u = if ($State.last) { $State.last } else { Get-Usual }
    $b = $BrandById[$u.brand]
    $f = if ($b) { Find-Flavor $b $u.flavor } else { $null }
    $img = Get-CanImage $u.brand $(if ($f) { $f.slug } else { '' })
    $h = [int]($FloatSize * 0.72); $w = [int]($h * 120 / 220)
    $gr.DrawImage($img, [int](($FloatSize - $w) / 2), [int](($FloatSize - $h) / 2), $w, $h)
})
$script:Drag = $null
$Float.Add_MouseDown({
    param($s, $e)
    if ($e.Button -eq 'Left') { $script:Drag = @{ start = [System.Windows.Forms.Cursor]::Position; origin = $Float.Location; moved = $false } }
})
$Float.Add_MouseMove({
    if (-not $script:Drag) { return }
    $p = [System.Windows.Forms.Cursor]::Position
    $dx = $p.X - $script:Drag.start.X; $dy = $p.Y - $script:Drag.start.Y
    if (-not $script:Drag.moved -and ([Math]::Abs($dx) + [Math]::Abs($dy)) -lt (Px 5)) { return }
    $script:Drag.moved = $true
    $Float.Location = New-Object System.Drawing.Point(($script:Drag.origin.X + $dx), ($script:Drag.origin.Y + $dy))
})
$Float.Add_MouseUp({
    param($s, $e)
    if ($e.Button -eq 'Right') { $TrayMenu.Show([System.Windows.Forms.Cursor]::Position); return }
    $d = $script:Drag; $script:Drag = $null
    if (-not $d) { return }
    if ($d.moved) { $State.floatX = $Float.Left; $State.floatY = $Float.Top; Save-State }
    else { Open-Picker }
})
function Update-Float {
    if (-not $State.showFloat) { $Float.Hide(); return }
    $x = $State.floatX; $y = $State.floatY
    $onScreen = $false
    foreach ($scr in [System.Windows.Forms.Screen]::AllScreens) {
        if ($scr.WorkingArea.Contains((New-Object System.Drawing.Point(($x + 10), ($y + 10))))) { $onScreen = $true }
    }
    if (-not $onScreen) {
        $wa = [System.Windows.Forms.Screen]::PrimaryScreen.WorkingArea
        $x = $wa.Right - $FloatSize - (Px 24); $y = $wa.Bottom - $FloatSize - (Px 120)
    }
    $Float.Location = New-Object System.Drawing.Point($x, $y)
    if (-not $Float.Visible) { $Float.Show() }
    $Float.Invalidate()
}

# ---------------------------------------------------------------- hotkeys
$MOD_ALT = 0x1; $MOD_CONTROL = 0x2; $MOD_NOREPEAT = 0x4000
$Hotkeys = New-Object SWHotkeys
$okPick = [SWNative]::RegisterHotKey($Hotkeys.Handle, 1, ($MOD_CONTROL -bor $MOD_ALT -bor $MOD_NOREPEAT), 0x44)   # D
$okUsual = [SWNative]::RegisterHotKey($Hotkeys.Handle, 2, ($MOD_CONTROL -bor $MOD_ALT -bor $MOD_NOREPEAT), 0x55)  # U
$Hotkeys.Add_Pressed({
    if ($Hotkeys.LastId -eq 1) { Open-Picker }
    elseif ($Hotkeys.LastId -eq 2) { Remember-Foreground; $x = Get-Usual; Give-Drink $x.brand $x.flavor }
})

Update-TrayMenu
Update-Float
$msg = 'Drag the floating can anywhere. Click it (or press Ctrl+Alt+D) to pick a drink. Ctrl+Alt+U gives your usual.'
if (-not ($okPick -and $okUsual)) { $msg = 'Running in your tray, but another app already uses Ctrl+Alt+D or Ctrl+Alt+U. Click the tray can instead.' }
$Tray.ShowBalloonTip(5000, "$Bolt Second Wind", $msg, [System.Windows.Forms.ToolTipIcon]::Info)

try {
    [System.Windows.Forms.Application]::Run()
} finally {
    [void][SWNative]::UnregisterHotKey($Hotkeys.Handle, 1)
    [void][SWNative]::UnregisterHotKey($Hotkeys.Handle, 2)
    $Tray.Visible = $false
    $Tray.Dispose()
    $script:Mutex.ReleaseMutex()
}
