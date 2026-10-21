# Google Play Store Deployment Guide — RecompIQ (`com.recompiq.app`)

This bundle includes everything needed to compile a signed **Android App Bundle (`.aab`)** and publish **RecompIQ** to the Google Play Console.

---

## Route A: Native Offline-First Android App via Capacitor (Recommended)
Capacitor wraps the `www/` app inside a native Android project so it works 100% offline without needing web hosting.

### Step 1: Initialize & Sync the Android Project
Requires Node.js (v18+) and Android Studio (Ladybug / Koala or newer):
```bash
npm install
npx cap add android
npx cap sync android
npx cap open android
```

### Step 2: Generate a Signed `.aab` in Android Studio
1. In Android Studio, select **Build → Generate Signed App Bundle / APK...**
2. Select **Android App Bundle** and click **Next**.
3. Click **Create new...** under Key store path:
   - **Key store path:** `recompiq-release-key.jks`
   - **Alias:** `recompiq`
   - **Validity:** `25 years`
4. Select the **release** build variant and click **Create**.
5. Your signed bundle will be output at:
   `android/app/release/app-release.aab`

---

## Route B: Trusted Web Activity (TWA) via Bubblewrap CLI
If you host the `www/` folder on HTTPS (e.g., Cloudflare Pages, Vercel, Firebase Hosting, or GitHub Pages):
```bash
npm i -g @bubblewrap/cli
bubblewrap build
```
Bubblewrap uses `twa-manifest.json` to output `app-release-bundle.aab` and `app-release-signed.apk`. Copy your SHA-256 signing fingerprint into `www/.well-known/assetlinks.json`.

---

## Google Play Console Checklist & Pre-Built Store Assets
1. **Store Graphics (Included in `play_store_assets/`):**
   - **Hi-Res App Icon (`512×512` PNG):** `play_store_assets/hi_res_icon_512x512.png`
   - **Feature Graphic (`1024×500` PNG):** `play_store_assets/feature_graphic_1024x500.png`
2. **Data Safety Questionnaire Answers:**
   - *Does your app collect or share any of the required user data types?* → **No** (All biometric, workout, and nutrition logs remain 100% on-device in local storage).
3. **Health Apps Declaration:**
   - Select **Fitness & Weight Management / Nutrition Tracker** (non-medical consumer wellness tool).
4. **Target SDK:** API Level 35 (Android 15) configured out of the box by Capacitor 6.
