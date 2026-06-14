# Going live with GitHub Pages

GitHub Pages serves static files for free over https — perfect here, because the
whole app is `index.html` + `data/fish.geojson` and needs no server or token.

You'll do this **once**. After that, every `git push` updates the live site.

---

## 0. One-time GitHub setup (skip if done)

- Have a GitHub account (github.com).
- Install Git if needed — macOS already has it (`git --version`).

---

## 1. Create an empty repo on GitHub

1. Go to **https://github.com/new**
2. Repository name: **`fishtagged`**
3. Visibility: **Public** (required for free Pages)
4. **Do NOT** check "Add a README" / .gitignore / license — keep it empty.
5. Click **Create repository**.

Leave that page open — it shows the repo URL you'll paste below
(`https://github.com/<your-username>/fishtagged.git`).

---

## 2. Push this folder up

Open Terminal and run these from this project folder
(`/Users/danielsuh/Downloads/Fishtagged`). **The repo is already initialized and
committed for you** — you only need to connect it and push.

```bash
cd /Users/danielsuh/Downloads/Fishtagged

# connect to your new GitHub repo (replace <your-username>)
git remote add origin https://github.com/<your-username>/fishtagged.git

git branch -M main
git push -u origin main
```

If it asks for a password, use a **Personal Access Token** (github.com →
Settings → Developer settings → Personal access tokens → Tokens (classic) →
Generate, scope `repo`), or sign in through the browser popup.

---

## 3. Turn on Pages

1. On GitHub, open your repo → **Settings** (top tab).
2. Left sidebar → **Pages**.
3. Under **Build and deployment → Source**, choose **Deploy from a branch**.
4. Branch: **`main`**, folder: **`/ (root)`** → **Save**.
5. Wait ~1 minute. The page shows:
   **Your site is live at `https://<your-username>.github.io/fishtagged/`**

That URL is your live demo. Open it on any device — phone, the projector, anywhere.

---

## 4. Updating it later

Any change (new data, tweaks) goes live with:

```bash
git add -A
git commit -m "describe the change"
git push
```

Give it ~1 minute, then refresh the live URL.

---

## Troubleshooting

- **Blank page / "couldn't load data"** — make sure `data/fish.geojson` was
  pushed (`git status` should be clean; the file is ~1.5 MB).
- **404 at the URL** — Pages can take 1–2 minutes the first time; also confirm
  Settings → Pages shows branch `main` / `/ (root)`.
- **Map tiles don't draw** — the basemap loads from CARTO/Esri over https; a
  corporate network that blocks them would affect it. Test on normal Wi-Fi.
