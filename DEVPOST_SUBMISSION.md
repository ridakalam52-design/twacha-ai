# TwachaAI · त्वचा AI

**Tagline:** A selfie skin check for India: YouCam AI scores your skin, and you get a routine from the chemist shelf that fits your monthly budget.

## Inspiration

*Twacha* (त्वचा) is Hindi for skin. In India, skincare advice comes from three places: a cousin, an influencer, or a ₹1,000 dermatologist visit that many people put off. The result is a bathroom shelf of products bought on hype, often wrong for the skin type and the city. Humid Mumbai skin, dry Jaipur skin and Delhi-smog skin need different things. We wanted something that starts from what your skin actually shows, speaks your language, and respects a student's ₹500 a month as much as a ₹3,000 budget.

## What it does

1. You upload a selfie (or use the camera with a face guide), pick a monthly budget (₹500 / ₹1,500 / ₹3,000) and your climate (humid / dry / polluted metro).
2. The **YouCam Skin Analysis API** scores 8 concerns: hydration, oil balance, acne, pores, redness, texture, dark circles and spots.
3. You get a **report card**: each concern with a score, a Good / Watch / Focus level and a one-line explanation in **English or Hindi**. Tap a concern to see YouCam's overlay of *where* it shows on your face.
4. A **deterministic routine engine** turns scores into an AM/PM routine by ingredient (salicylic acid for acne, niacinamide for oil and pores, vitamin C or alpha arbutin for spots, ceramides and hyaluronic acid for dryness), with sunscreen SPF 50 PA++++ every morning.
5. It fills each step with **real, widely sold Indian products** (Minimalist, The Derma Co, Dot & Key, Cetaphil, Re'equil, Plum, Lakmé and more) and keeps the **monthly cost under your budget**. Whatever doesn't fit is shown as "add later". Switch budget or climate and the plan updates instantly.
6. **Re-scan in 4 weeks** and see per-concern progress, stored privately on your device. One tap adds a calendar reminder.
7. Clear safety copy throughout: it's a cosmetic check, not medical advice, and very low acne scores prompt a dermatologist visit.

## How we built it

- **Backend:** FastAPI (Python 3.12). The YouCam V2 flow runs fully server-side so the API key never reaches the browser: `POST /s2s/v2.0/file` → `PUT` the bytes to the presigned URL with the returned headers → `POST /s2s/v2.0/task/skin-analysis` with `src_file_id`, `dst_actions`, `miniserver_args.enable_mask_overlay` and `format: "json"` → poll `GET /s2s/v2.0/task/skin-analysis/{task_id}`.
- **Image prep:** Pillow fixes EXIF rotation and downscales to ≤ 2560 px, then picks **HD actions** (`hd_moisture`, `hd_pore`…) when the short side is ≥ 1080 px and **SD actions** (`moisture`, `pore`, `dark_circle_v2`…) otherwise. SD and HD are never mixed.
- **Score handling:** we display YouCam's `ui_score` and rank priorities on `raw_score`; region-aware HD results (pores by forehead / nose / cheek) are kept as detail.
- **Routine engine:** pure Python rules with no LLM, so the same scores, budget and climate always give the same routine. It handles skin-type detection, sensitivity (skip acids when redness is high), climate nudges, actives that shouldn't share a night, and a per-budget cap on serums.
- **Budget fitting:** each product has an approximate MRP and how many months it lasts; essentials go in first at the cheapest suitable price, treatments are added by severity while the monthly total fits, and leftover budget upgrades the essentials to better-matched picks.
- **Frontend:** static HTML/CSS/JS with no build step, mobile-first, camera capture via `getUserMedia`, an EN/हिंदी toggle and `localStorage` history.
- **Quality:** a pytest suite covers the routine engine across every budget × climate × skin profile, the YouCam client with mocked HTTP (success, engine errors, 401, bad parameters, upload failure, timeout), the API endpoints, real captured YouCam responses, and a repo-hygiene check that `.env` is never tracked.

## Challenges we ran into

- **Making ₹500 honest.** A good SPF 50 PA++++ sunscreen alone costs about ₹270 a month when used generously. Instead of pretending a 6-step routine fits, the engine guarantees the three essentials and shows what to add when the budget allows.
- **Two kinds of score.** `ui_score` is deliberately encouraging, while `raw_score` is the model's direct prediction. In real responses a hydration `raw_score` of 31 came back as `ui_score` 63. Showing one and prioritising on the other kept the UI kind without hiding real concerns.
- **HD vs SD.** They can't be mixed and have different minimum resolutions, so the server picks one per photo after resizing.
- **Hindi copy** had to be plain and natural, not a literal translation of cosmetic jargon.

## Accomplishments that we're proud of

- An end-to-end YouCam integration verified against the live API, with real HD and SD responses used as test fixtures.
- A routine engine that is explainable: every product says which concern it's for.
- A budget promise that is tested for every budget, climate and skin profile.
- A demo mode built on a real response, so judges can try it without a key.

## What we learned

- YouCam's async task model (file → upload → task → poll) and its engine error codes, which map neatly to friendly retake tips ("move closer", "find better light").
- How region-level HD results (pores by forehead, nose, cheek) can make advice more specific.
- That a deterministic rules engine is easier to trust, test and explain than a generated routine.

## What's next

- Live prices and stock from Indian retailers (Nykaa, Amazon, Tira) and affiliate checkout.
- YouCam **Skin Simulation** to preview what four weeks of the routine could look like.
- More Indian languages (Tamil, Bengali, Marathi) and voice explanations.
- Opt-in cloud sync for progress, and a "share with my dermatologist" PDF.

## Built with

`python` · `fastapi` · `uvicorn` · `httpx` · `pillow` · `pytest` · `html` · `css` · `javascript` · `youcam-api` · `perfect-corp-skin-analysis`
