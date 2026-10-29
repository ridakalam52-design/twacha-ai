# TwachaAI · 2.5-minute demo script

Total ≈ 2:30. Record on a phone-sized browser window (or real phone) with the server in **live** mode (`YOUCAM_API_KEY` set). Have one good selfie ready: front-facing, no makeup, window light.

---

### 0:00 – 0:15 · Hook
**Screen:** TwachaAI home page.
**Say:** "Twacha means skin in Hindi. Most people in India pick skincare from ads or a cousin's advice. TwachaAI starts from what your skin actually shows, using the YouCam Skin Analysis API, and builds a routine that fits your monthly budget."

### 0:15 – 0:40 · Scan
**Screen:** Tap **Use camera** (show the face guide) or **Upload photo**. Pick **₹1,500** and **Polluted metro**. Tap **Check my skin**.
**Say:** "One selfie, a budget, and your city's climate. The photo goes to our server, never straight from the browser with a key. We resize it to YouCam's spec, choose HD or SD analysis, upload it, start a skin-analysis task for eight concerns and poll until it's done."
**Screen:** Loading steps tick through, then results appear.

### 0:40 – 1:10 · Report card
**Screen:** Skin score ring, skin type, top focus. Scroll the report card.
**Say:** "Here's the report card: hydration, oil, acne, pores, redness, texture, dark circles and spots. Each has YouCam's score, a level, and a plain-language explanation."
**Screen:** Tap **See where on your face** on the top concern; show the overlay image.
**Say:** "YouCam also returns an overlay, so you can see where the issue shows on your face."
**Screen:** Tap **हिंदी** in the top bar. Scroll briefly. Switch back.
**Say:** "Everything works in Hindi too."

### 1:10 – 1:45 · Routine and budget
**Screen:** Routine card, **Morning** then **Night** tabs.
**Say:** "The routine engine is deterministic: concerns map to ingredients, like salicylic acid for acne and niacinamide for oil, and sunscreen SPF 50 PA++++ is always in the morning. It knows not to stack two acids on the same night."
**Screen:** Shopping list with the budget meter.
**Say:** "Each step uses a real product you can buy in India, with approximate MRP and how long it lasts, so the monthly cost stays under ₹1,500."
**Screen:** Tap **₹500**, then **₹3,000**.
**Say:** "Change the budget and the plan re-fits instantly, without calling the API again. At ₹500 you get the essentials and a clear 'add later' list. Nothing is hidden."

### 1:45 – 2:10 · Progress and safety
**Screen:** 4-week progress card (show a second scan's deltas if you have one; otherwise the "re-scan around …" message). Tap **Add re-scan reminder**.
**Say:** "Every scan is saved privately on your phone. Come back in four weeks and you'll see what improved, concern by concern. One tap adds a calendar reminder."
**Screen:** Scroll to the disclaimer; if available, show the dermatologist banner from a low-acne demo scan.
**Say:** "It's a cosmetic check, not medical advice. When acne scores are very low, we tell you to see a dermatologist."

### 2:10 – 2:30 · Close
**Screen:** Footer: "Powered by YouCam Skin Analysis API" with the action chips.
**Say:** "Under the hood: FastAPI, a server-side YouCam V2 client verified against the live API, a tested routine engine, and a demo mode built on a real YouCam response. TwachaAI: your skin, your language, your budget."

---

**Backup plan:** if the network or API is slow, restart the server without `YOUCAM_API_KEY`. The app runs in demo mode with a clear "Demo data" label, built on a real captured YouCam response.
