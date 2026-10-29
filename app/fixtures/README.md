# Real YouCam responses

`youcam_skin_analysis_hd.json` and `youcam_skin_analysis_sd.json` are real responses from
`GET /s2s/v2.0/task/skin-analysis/{task_id}` (status `success`, `format: "json"`,
`miniserver_args.enable_mask_overlay: true`), captured on 29 Oct 2026 from
`https://yce-api-01.makeupar.com`.

- HD run: 1450x1933 JPEG, actions `hd_moisture, hd_oiliness, hd_acne, hd_pore, hd_redness, hd_texture, hd_dark_circle, hd_age_spot`.
- SD run: the same photo at 900x1200, actions `moisture, oiliness, acne, pore, redness, texture, dark_circle_v2, age_spot`.
- Source photo: NASA official portrait of astronaut Sunita Williams (2018), public domain,
  via Wikimedia Commons ("Sunita Williams in 2018 (cropped).jpg"). The photo itself is not
  stored in this repo; only the scores.
- Presigned query strings were removed from `mask_urls`, so those links no longer load.
  Every other field and value is exactly what the API returned (re-indented).

Used by the test suite and as the base for demo mode (`app/mock.py`).
