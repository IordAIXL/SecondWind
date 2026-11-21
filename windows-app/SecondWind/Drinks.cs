// Brand data, saved settings, and the drink message.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;

namespace SecondWind
{
    public sealed class Flavor
    {
        public string Name;
        public string Slug;
    }

    public sealed class Purpose
    {
        public string Mode;
        public string For;
        public List<string> How = new List<string>();
    }

    public sealed class Brand
    {
        public string Id;
        public string Name;
        public string Size;
        public string Sip;
        public string Vibe;
        public Purpose Purpose;
        public List<Flavor> Flavors = new List<Flavor>();

        public Flavor Find(string flavor)
        {
            return Flavors.FirstOrDefault(f => string.Equals(f.Name, flavor, StringComparison.OrdinalIgnoreCase));
        }
    }

    public sealed class Drink
    {
        public string Brand;
        public string Flavor;
        public Drink(string brand, string flavor) { Brand = brand; Flavor = flavor; }
        public bool Same(string brand, string flavor)
        {
            return Brand == brand && string.Equals(Flavor, flavor, StringComparison.OrdinalIgnoreCase);
        }
    }

    public static class Catalog
    {
        public static string Version = "0.0.0";
        public static string DefaultId = "redbull";
        public static List<Brand> Brands = new List<Brand>();
        public static Dictionary<string, Brand> ById = new Dictionary<string, Brand>();

        public static string AssetDir { get { return Path.Combine(AppContext.BaseDirectory, "Assets"); } }

        public static void Load()
        {
            var root = JsonNode.Parse(File.ReadAllText(Path.Combine(AssetDir, "data.json"), Encoding.UTF8));
            Version = (string)root["version"] ?? Version;
            DefaultId = (string)root["default"] ?? DefaultId;
            foreach (var n in root["brands"].AsArray())
            {
                var b = new Brand
                {
                    Id = (string)n["id"],
                    Name = (string)n["name"],
                    Size = (string)n["size"] ?? "",
                    Sip = (string)n["sip"] ?? "",
                    Vibe = (string)n["vibe"] ?? "",
                };
                var p = n["purpose"];
                if (p != null && p["mode"] != null)
                {
                    b.Purpose = new Purpose { Mode = (string)p["mode"], For = (string)p["for"] ?? "" };
                    if (p["how"] is JsonArray how) foreach (var h in how) b.Purpose.How.Add((string)h);
                }
                foreach (var f in n["flavors"].AsArray())
                    b.Flavors.Add(new Flavor { Name = (string)f["name"], Slug = (string)f["slug"] });
                Brands.Add(b);
                ById[b.Id] = b;
            }
        }

        public static Brand Get(string id)
        {
            Brand b;
            if (id != null && ById.TryGetValue(id, out b)) return b;
            return ById.TryGetValue(DefaultId, out b) ? b : Brands[0];
        }
    }

    // Saved in %LOCALAPPDATA% (Windows keeps it inside the app's own storage).
    public sealed class Settings
    {
        public int Total;
        public bool AutoSend;
        public bool ShowFloat = true;
        public int FloatX = -1;
        public int FloatY = -1;
        public List<Drink> Favorites = new List<Drink>();
        public Drink Last;

        static string Dir { get { return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "SecondWind"); } }
        static string FilePath { get { return Path.Combine(Dir, "settings.json"); } }

        public static Settings Load()
        {
            var s = new Settings();
            try
            {
                if (!File.Exists(FilePath)) return s;
                var r = JsonNode.Parse(File.ReadAllText(FilePath, Encoding.UTF8));
                s.Total = (int?)r["total"] ?? 0;
                s.AutoSend = (bool?)r["autoSend"] ?? false;
                s.ShowFloat = (bool?)r["showFloat"] ?? true;
                s.FloatX = (int?)r["floatX"] ?? -1;
                s.FloatY = (int?)r["floatY"] ?? -1;
                if (r["favorites"] is JsonArray favs)
                    foreach (var f in favs) s.Favorites.Add(new Drink((string)f["brand"], (string)f["flavor"]));
                if (r["last"] is JsonObject last) s.Last = new Drink((string)last["brand"], (string)last["flavor"]);
            }
            catch { }
            return s;
        }

        public void Save()
        {
            try
            {
                Directory.CreateDirectory(Dir);
                var favs = new JsonArray();
                foreach (var f in Favorites) favs.Add(new JsonObject { ["brand"] = f.Brand, ["flavor"] = f.Flavor });
                var o = new JsonObject
                {
                    ["total"] = Total,
                    ["autoSend"] = AutoSend,
                    ["showFloat"] = ShowFloat,
                    ["floatX"] = FloatX,
                    ["floatY"] = FloatY,
                    ["favorites"] = favs,
                    ["last"] = Last == null ? null : new JsonObject { ["brand"] = Last.Brand, ["flavor"] = Last.Flavor },
                };
                File.WriteAllText(FilePath, o.ToJsonString(new JsonSerializerOptions { WriteIndented = true }), new UTF8Encoding(false));
            }
            catch { }
        }

        public bool IsFav(string brand, string flavor) { return Favorites.Any(f => f.Same(brand, flavor)); }

        public void ToggleFav(string brand, string flavor)
        {
            if (IsFav(brand, flavor)) Favorites.RemoveAll(f => f.Same(brand, flavor));
            else Favorites.Add(new Drink(brand, flavor));
            Save();
        }

        // The first favorite is "the usual".
        public void MakeUsual(string brand, string flavor)
        {
            Favorites.RemoveAll(f => f.Same(brand, flavor));
            Favorites.Insert(0, new Drink(brand, flavor));
            Save();
        }

        public Drink Usual()
        {
            if (Favorites.Count > 0) return Favorites[0];
            if (Last != null) return Last;
            var b = Catalog.Get(null);
            return new Drink(b.Id, b.Flavors[0].Name);
        }
    }

    public static class DrinkMessage
    {
        const string Bolt = "⚡";

        public static string Build(Brand b, string flavor, bool known, int n)
        {
            var l = new List<string>();
            l.Add(Bolt + " Second Wind: *slides you an ice-cold " + b.Name + " " + flavor + " (" + b.Size + ")*");
            if (known) l.Add("Crack it open! Open with \"" + b.Sip + "\" and then one short line on how " + flavor + " tastes.");
            else l.Add("Crack it open! (Fun fact: I'm not sure " + b.Name + " even makes " + flavor + ". React to that, then drink it anyway.) One short line on how it tastes.");
            var p = b.Purpose;
            if (p != null)
            {
                var how = p.How.Count > 0 ? " Work style: " + string.Join(" ", p.How) : "";
                l.Add("Mode: " + p.Mode + ". " + p.For + how);
            }
            var tail = ".";
            if (n == 1) tail = ". First one!";
            else if (new[] { 5, 10, 25, 50, 100 }.Contains(n)) tail = ". Milestone!";
            l.Add("That's drink #" + n + " I've handed you" + tail);
            l.Add("");
            l.Add("Now get your second wind. Refocus on our real work and print this, short and honest:");
            l.Add(Bolt + " DIALED IN" + (p != null ? " · " + p.Mode : ""));
            l.Add("Goal: <what we are actually trying to do>");
            l.Add("Done: <what is finished so far>");
            l.Add("Left: <what is still open>");
            l.Add("Dropping: <tangents we are parking, or nothing>");
            l.Add("Next step: <the single next concrete action>");
            l.Add("");
            l.Add("Then do that next step right away: fewer words, no tangents. If there's no task yet, ask me one crisp question. (Pretend drink, just for fun.)");
            return string.Join("\r\n", l);
        }
    }
}
