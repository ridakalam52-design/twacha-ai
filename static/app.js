/* TwachaAI front end. No build step, no framework. The YouCam key never touches the browser:
   the selfie goes to our own /api/analyze, which calls YouCam server-side. */
(() => {
  "use strict";

  const HISTORY_KEY = "twacha.scans.v1";
  const RESCAN_DAYS = 28;
  const $ = (id) => document.getElementById(id);

  const I18N = {
    en: {
      eyebrow: "Selfie skin check · made for Indian skin",
      heroTitle: "Know your skin in a minute. Get a routine that fits your wallet.",
      heroLede: "One selfie, eight skin concerns, a plain-language report card and an AM/PM routine from brands you can buy at the chemist.",
      step1: "Your selfie", step2: "Monthly budget", step3: "Your city's climate",
      dropHint: "Front-facing, no makeup, even light", upload: "Upload photo", useCamera: "Use camera", snap: "Take photo", stopCamera: "Close camera",
      tip1: "Face fills most of the frame", tip2: "Glasses off, hair off the forehead", tip3: "Face a window or soft light",
      humid: "Humid", humidEg: "Mumbai, Chennai, Kolkata", dry: "Dry", dryEg: "Jaipur, Ahmedabad, Hyderabad",
      polluted: "Polluted metro", pollutedEg: "Delhi NCR, Kanpur, Lucknow",
      analyze: "Check my skin", privacy: "Your photo is sent securely to the YouCam API for analysis and is not stored by TwachaAI.",
      prog1: "Preparing your photo", prog2: "Uploading securely to YouCam", prog3: "Analysing 8 skin concerns", prog4: "Building your routine",
      demoTitle: "Demo data", demoBody: "No YouCam API key is set on this server, so these scores are realistic samples, not a real analysis of your photo.",
      overall: "Skin score", skinType: "Skin type", skinAge: "Skin age (AI estimate)", topFocus: "Top focus",
      dermTitle: "Consider a dermatologist", dermBody: "Your acne score is low. If breakouts are painful, cystic or leave marks, a dermatologist can prescribe treatment that over-the-counter products can't.",
      reportTitle: "Your skin report card", reportSub: "Higher is healthier. Sorted by what needs care first.", close: "Close",
      progressTitle: "4-week progress", addReminder: "Add re-scan reminder", clearHistory: "Clear scan history",
      routineTitle: "Your routine", morning: "☀ Morning", night: "☾ Night",
      shopTitle: "Shopping list", laterTitle: "Add later", newScan: "New scan",
      powered: "Powered by YouCam Skin Analysis API",
      disclaimer: "TwachaAI is a cosmetic skin check, not medical advice. For painful, cystic or scarring acne, sudden rashes, or a changing mole, please see a dermatologist.",
      level: { good: "Good", watch: "Watch", focus: "Focus" },
      type: { oily: "Oily", dry: "Dry", normal: "Normal", combination: "Combination" },
      sensitiveSuffix: " · sensitive",
      viewMask: "See where on your face →",
      firstScan: (d) => `First scan saved on this device. Re-scan around ${d} to see your progress.`,
      compared: (d, n) => `Compared with your scan on ${d} (${n} day${n === 1 ? "" : "s"} ago).`,
      nextDue: (d) => ` Next check due ${d}.`,
      overallRow: "Overall score",
      perMonth: "/month", upfront: "upfront",
      budgetLine: (m, b, u) => `About ₹${m} a month of your ₹${b} budget · ₹${u} to buy everything once.`,
      lasts: (m) => `lasts ~${m} mo`,
      find: "Find online →",
      forLabel: "for",
      skippedBudget: "doesn't fit this budget yet",
      skippedCap: "kept out so you don't overload your skin; add after 4 weeks",
      demoLabel: "Demo", liveLabel: "Live API",
      errGeneric: "Something went wrong. Please try again.",
      errCamera: "Camera not available. Please upload a photo instead.",
      reminderTitle: "TwachaAI: re-scan your skin",
      concerns: { pollution: "pollution", dry_climate: "dry climate", cleanser: "cleanser", moisturizer: "moisturiser", sunscreen: "sun protection" },
      cleared: "Scan history cleared.",
    },
    hi: {
      eyebrow: "सेल्फ़ी स्किन जांच · भारतीय त्वचा के लिए",
      heroTitle: "एक मिनट में अपनी त्वचा जानें। अपने बजट में रूटीन पाएं।",
      heroLede: "एक सेल्फ़ी, त्वचा की 8 बातें, आसान भाषा में रिपोर्ट कार्ड और सुबह-रात का रूटीन, उन ब्रांड्स से जो आपके केमिस्ट पर मिलते हैं।",
      step1: "आपकी सेल्फ़ी", step2: "महीने का बजट", step3: "आपके शहर का मौसम",
      dropHint: "सामने से, बिना मेकअप, अच्छी रोशनी में", upload: "फ़ोटो अपलोड करें", useCamera: "कैमरा खोलें", snap: "फ़ोटो लें", stopCamera: "कैमरा बंद करें",
      tip1: "चेहरा फ़्रेम का ज़्यादातर हिस्सा भरे", tip2: "चश्मा हटाएं, बाल माथे से हटाएं", tip3: "खिड़की या हल्की रोशनी की ओर देखें",
      humid: "उमस भरा", humidEg: "मुंबई, चेन्नई, कोलकाता", dry: "सूखा", dryEg: "जयपुर, अहमदाबाद, हैदराबाद",
      polluted: "प्रदूषित महानगर", pollutedEg: "दिल्ली NCR, कानपुर, लखनऊ",
      analyze: "मेरी त्वचा जांचें", privacy: "आपकी फ़ोटो जांच के लिए सुरक्षित रूप से YouCam API को भेजी जाती है और TwachaAI इसे सेव नहीं करता।",
      prog1: "फ़ोटो तैयार हो रही है", prog2: "YouCam पर सुरक्षित अपलोड", prog3: "त्वचा की 8 बातों की जांच", prog4: "आपका रूटीन बन रहा है",
      demoTitle: "डेमो डेटा", demoBody: "इस सर्वर पर YouCam API key नहीं है, इसलिए ये स्कोर नमूना हैं, आपकी फ़ोटो की असली जांच नहीं।",
      overall: "स्किन स्कोर", skinType: "त्वचा का प्रकार", skinAge: "त्वचा की उम्र (AI अनुमान)", topFocus: "सबसे ज़रूरी",
      dermTitle: "त्वचा विशेषज्ञ से मिलें", dermBody: "आपका मुंहासों का स्कोर कम है। अगर मुंहासे दर्द वाले, गहरे या दाग़ छोड़ने वाले हैं, तो डर्मेटोलॉजिस्ट ऐसा इलाज दे सकते हैं जो दुकान के प्रोडक्ट नहीं दे सकते।",
      reportTitle: "आपका स्किन रिपोर्ट कार्ड", reportSub: "ज़्यादा स्कोर यानी बेहतर। पहले वो जिन पर ध्यान चाहिए।", close: "बंद करें",
      progressTitle: "4 हफ़्ते की प्रगति", addReminder: "दोबारा जांच का रिमाइंडर", clearHistory: "पुरानी जांच मिटाएं",
      routineTitle: "आपका रूटीन", morning: "☀ सुबह", night: "☾ रात",
      shopTitle: "ख़रीदारी सूची", laterTitle: "बाद में जोड़ें", newScan: "नई जांच",
      powered: "YouCam Skin Analysis API द्वारा संचालित",
      disclaimer: "TwachaAI एक कॉस्मेटिक स्किन जांच है, चिकित्सा सलाह नहीं। दर्द वाले, गहरे या दाग़ छोड़ने वाले मुंहासे, अचानक चकत्ते, या बदलते तिल के लिए त्वचा विशेषज्ञ से मिलें।",
      level: { good: "अच्छा", watch: "ध्यान दें", focus: "ज़रूरी" },
      type: { oily: "तैलीय", dry: "रूखी", normal: "सामान्य", combination: "मिश्रित" },
      sensitiveSuffix: " · संवेदनशील",
      viewMask: "चेहरे पर कहाँ है, देखें →",
      firstScan: (d) => `पहली जांच इस डिवाइस पर सेव हो गई। प्रगति देखने के लिए ${d} के आसपास दोबारा जांच करें।`,
      compared: (d, n) => `${d} की जांच से तुलना (${n} दिन पहले)।`,
      nextDue: (d) => ` अगली जांच ${d} को।`,
      overallRow: "कुल स्कोर",
      perMonth: "/महीना", upfront: "एक बार में",
      budgetLine: (m, b, u) => `₹${b} के बजट में लगभग ₹${m} महीना · सब एक बार ख़रीदने पर ₹${u}।`,
      lasts: (m) => `~${m} महीने चलेगा`,
      find: "ऑनलाइन देखें →",
      forLabel: "के लिए",
      skippedBudget: "इस बजट में अभी नहीं आता",
      skippedCap: "त्वचा पर ज़्यादा बोझ न हो, इसलिए 4 हफ़्ते बाद जोड़ें",
      demoLabel: "डेमो", liveLabel: "लाइव API",
      errGeneric: "कुछ गड़बड़ हुई। कृपया फिर से कोशिश करें।",
      errCamera: "कैमरा उपलब्ध नहीं है। कृपया फ़ोटो अपलोड करें।",
      reminderTitle: "TwachaAI: त्वचा की दोबारा जांच",
      concerns: { pollution: "प्रदूषण", dry_climate: "सूखा मौसम", cleanser: "सफ़ाई", moisturizer: "नमी", sunscreen: "धूप से बचाव" },
      cleared: "पुरानी जांच मिटा दी गई।",
    },
  };

  const state = {
    lang: localStorage.getItem("twacha.lang") || "en",
    file: null,
    stream: null,
    result: null,
    tab: "am",
    previous: null,
    config: null,
  };
  const t = (k) => I18N[state.lang][k];
  const L = (obj) => (obj && typeof obj === "object" ? obj[state.lang] || obj.en : obj);
  const fmtDate = (d) => d.toLocaleDateString(state.lang === "hi" ? "hi-IN" : "en-IN", { day: "numeric", month: "short", year: "numeric" });
  const inr = (n) => Number(n).toLocaleString("en-IN");
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  /* ---------------- i18n ---------------- */
  function applyLang() {
    document.documentElement.lang = state.lang;
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const v = t(el.dataset.i18n);
      if (typeof v === "string") el.textContent = v;
    });
    $("langToggle").textContent = state.lang === "en" ? "हिंदी" : "English";
    $("disclaimer").textContent = t("disclaimer");
    setModeBadge();
    if (state.stream) $("cameraBtn").querySelector("span").textContent = t("stopCamera");
    if (state.result) renderResult(state.result, false);
  }

  function setModeBadge() {
    const b = $("modeBadge");
    if (!state.config) return;
    const live = state.config.mode === "live";
    b.hidden = false;
    b.className = "badge " + (live ? "live" : "demo");
    b.textContent = live ? t("liveLabel") : t("demoLabel");
  }

  /* ---------------- photo input ---------------- */
  function setFile(blob) {
    state.file = blob;
    const url = URL.createObjectURL(blob);
    const img = $("preview");
    img.src = url;
    img.hidden = false;
    $("loadingImg").src = url;
    $("dropEmpty").hidden = true;
    $("analyzeBtn").disabled = false;
    $("formError").hidden = true;
  }

  function onFile(f) {
    if (!f) return;
    if (!/^image\/(jpeg|png)$/.test(f.type)) {
      showFormError(state.lang === "hi" ? "कृपया JPG या PNG फ़ोटो चुनें।" : "Please choose a JPG or PNG photo.");
      return;
    }
    stopCamera();
    setFile(f);
  }

  async function toggleCamera() {
    if (state.stream) return stopCamera();
    try {
      state.stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user", width: { ideal: 1440 }, height: { ideal: 1920 } },
        audio: false,
      });
      const v = $("camera");
      v.srcObject = state.stream;
      v.hidden = false;
      await v.play();
      $("preview").hidden = true;
      $("dropEmpty").hidden = true;
      $("dropzone").classList.add("live");
      $("snapBtn").hidden = false;
      $("cameraBtn").querySelector("span").textContent = t("stopCamera");
    } catch (e) {
      showFormError(t("errCamera"));
      stopCamera();
    }
  }

  function stopCamera() {
    if (state.stream) state.stream.getTracks().forEach((tr) => tr.stop());
    state.stream = null;
    $("camera").hidden = true;
    $("dropzone").classList.remove("live");
    $("snapBtn").hidden = true;
    $("cameraBtn").querySelector("span").textContent = t("useCamera");
    if (!state.file) $("dropEmpty").hidden = false;
  }

  function snap() {
    const v = $("camera");
    const c = $("snapCanvas");
    c.width = v.videoWidth;
    c.height = v.videoHeight;
    c.getContext("2d").drawImage(v, 0, 0);
    c.toBlob((blob) => { stopCamera(); setFile(new File([blob], "selfie.jpg", { type: "image/jpeg" })); }, "image/jpeg", 0.92);
  }

  function showFormError(msg) {
    const el = $("formError");
    el.textContent = msg;
    el.hidden = false;
  }

  /* ---------------- views ---------------- */
  function show(view) {
    ["scanView", "loadingView", "resultView"].forEach((id) => ($(id).hidden = id !== view));
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  let progTimer = null;
  function startProgress() {
    const items = [...$("progressSteps").children];
    items.forEach((li) => (li.className = ""));
    let i = 0;
    items[0].className = "active";
    const delays = [700, 1600, 6000];
    const next = () => {
      if (i >= items.length - 1) return;
      items[i].className = "done";
      i += 1;
      items[i].className = "active";
      progTimer = setTimeout(next, delays[i] || 4000);
    };
    progTimer = setTimeout(next, delays[0]);
  }
  function stopProgress() { clearTimeout(progTimer); }

  /* ---------------- analyze ---------------- */
  async function analyze(ev) {
    ev.preventDefault();
    if (!state.file) return;
    const fd = new FormData();
    fd.append("photo", state.file, state.file.name || "selfie.jpg");
    fd.append("budget", document.querySelector("input[name=budget]:checked").value);
    fd.append("climate", document.querySelector("input[name=climate]:checked").value);
    show("loadingView");
    startProgress();
    try {
      const res = await fetch("/api/analyze", { method: "POST", body: fd });
      const data = await res.json().catch(() => ({}));
      stopProgress();
      if (!res.ok) {
        show("scanView");
        showFormError((data.error && data.error.message) || t("errGeneric"));
        return;
      }
      state.tab = "am";
      renderResult(data, true);
      show("resultView");
    } catch (e) {
      stopProgress();
      show("scanView");
      showFormError(t("errGeneric"));
    }
  }

  /* ---------------- history (localStorage) ---------------- */
  const loadHistory = () => { try { return JSON.parse(localStorage.getItem(HISTORY_KEY)) || []; } catch { return []; } };
  const saveHistory = (h) => localStorage.setItem(HISTORY_KEY, JSON.stringify(h.slice(-12)));

  function recordScan(data) {
    const hist = loadHistory();
    state.previous = hist.length ? hist[hist.length - 1] : null;
    const scores = {};
    Object.entries(data.scores).forEach(([k, v]) => (scores[k] = v.ui_score));
    hist.push({ at: new Date().toISOString(), overall: data.overall, scores, demo: !!data.demo });
    saveHistory(hist);
  }

  /* ---------------- render ---------------- */
  function renderResult(data, fresh) {
    state.result = data;
    if (fresh) recordScan(data);
    const r = data.routine;

    $("demoBanner").hidden = !data.demo;
    const overall = data.overall ?? 0;
    $("overallScore").textContent = overall;
    requestAnimationFrame(() => ($("ringFg").style.strokeDashoffset = String(327 - (327 * overall) / 100)));
    $("skinType").textContent = t("type")[r.profile.type] + (r.profile.sensitive ? t("sensitiveSuffix") : "");
    $("skinAgeRow").hidden = data.skin_age == null;
    $("skinAge").textContent = data.skin_age ?? "–";
    const top = data.report.find((x) => x.level !== "good") || data.report[0];
    $("topFocus").textContent = top ? L(top.label) : "–";
    $("dermBanner").hidden = !r.flags.includes("see_dermatologist");

    // report card
    $("reportList").innerHTML = data.report.map((row) => `
      <li class="report-item">
        <div class="report-top">
          <h3>${esc(L(row.label))}</h3>
          <span class="level ${row.level}">${esc(t("level")[row.level])}</span>
          <span class="score">${row.ui_score}</span>
        </div>
        <div class="bar"><i class="${row.level}" data-w="${row.ui_score}"></i></div>
        <p>${esc(L(row.explain))}</p>
        ${row.mask_url ? `<button class="mask-link" type="button" data-mask="${esc(row.mask_url)}">${esc(t("viewMask"))}</button>` : ""}
      </li>`).join("");
    requestAnimationFrame(() => document.querySelectorAll(".bar > i").forEach((i) => (i.style.width = i.dataset.w + "%")));

    renderProgress(data);
    renderRoutine();
    renderShop(r);

    $("actionsUsed").innerHTML = (data.actions || []).map((a) => `<code>${esc(a)}</code>`).join("") +
      (data.quality ? `<code>${data.quality.toUpperCase()}</code>` : "");
  }

  function renderProgress(data) {
    const prev = state.previous;
    const now = new Date();
    const due = new Date(now.getTime() + RESCAN_DAYS * 864e5);
    const list = $("progressList");
    if (!prev) {
      $("progressSub").textContent = t("firstScan")(fmtDate(due));
      list.innerHTML = "";
      return;
    }
    const prevDate = new Date(prev.at);
    const days = Math.max(0, Math.round((now - prevDate) / 864e5));
    $("progressSub").textContent = t("compared")(fmtDate(prevDate), days) + t("nextDue")(fmtDate(due));
    const rows = [{ label: t("overallRow"), now: data.overall, was: prev.overall }];
    data.report.forEach((row) => rows.push({ label: L(row.label), now: row.ui_score, was: prev.scores[row.key] }));
    list.innerHTML = rows.filter((x) => x.was != null && x.now != null).map((x) => {
      const d = Math.round(x.now - x.was);
      const cls = d > 0 ? "up" : d < 0 ? "down" : "flat";
      const sign = d > 0 ? "+" : "";
      return `<li class="progress-item"><span>${esc(x.label)}</span><span>${x.was} → ${x.now} <b class="delta ${cls}">${sign}${d}</b></span></li>`;
    }).join("");
  }

  function renderRoutine() {
    const r = state.result.routine;
    document.querySelectorAll(".seg-btn").forEach((b) => b.classList.toggle("active", b.dataset.tab === state.tab));
    $("routineList").innerHTML = r[state.tab].map((s) => `
      <li class="routine-step">
        <div>
          <div class="kind">${esc(L(s.label))}</div>
          <div class="prod">${esc(s.product)}</div>
          <div class="how">${esc(L(s.how))}</div>
        </div>
      </li>`).join("");
    $("notesList").innerHTML = r.notes.map((n) => `<li>${esc(L(n))}</li>`).join("");
  }

  function concernName(key) {
    const row = state.result.report.find((x) => x.key === key);
    return row ? L(row.label) : (t("concerns")[key] || key);
  }

  function renderShop(r) {
    $("priceNote").textContent = r.price_note;
    document.querySelectorAll("#replanBudget .chip-btn").forEach((b) => b.classList.toggle("active", Number(b.dataset.budget) === r.budget));
    $("replanClimate").value = r.profile.climate;
    const pct = Math.min(100, Math.round((r.monthly_total / r.budget) * 100));
    $("budgetFill").style.width = pct + "%";
    $("budgetText").textContent = t("budgetLine")(inr(r.monthly_total), inr(r.budget), inr(r.upfront_total));
    $("productList").innerHTML = r.products.map((p) => `
      <li class="product">
        <div>
          <div class="brand-line">${esc(p.brand)}</div>
          <div class="pname">${esc(p.name)}</div>
          <div class="pmeta">${esc(p.size)} · ${esc(t("lasts")(p.months))}</div>
          <div>${p.for.map((c) => `<span class="tag">${esc(t("forLabel") === "for" ? "for " + concernName(c) : concernName(c) + " " + t("forLabel"))}</span>`).join("")}</div>
        </div>
        <div class="price">₹${inr(p.mrp)}<small>~₹${inr(p.monthly)}${esc(t("perMonth"))}</small></div>
        <a href="${esc(p.search_url)}" target="_blank" rel="noopener">${esc(t("find"))}</a>
      </li>`).join("");
    const box = $("skippedBox");
    box.hidden = !r.skipped.length;
    $("skippedList").innerHTML = r.skipped.map((s) =>
      `<li><b>${esc(L(s.label))}</b>: ${esc(s.reason === "budget" ? t("skippedBudget") : t("skippedCap"))}</li>`).join("");
  }

  async function replan(budget, climate) {
    const data = state.result;
    if (!data) return;
    try {
      const res = await fetch("/api/routine", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scores: data.scores, budget, climate }),
      });
      if (!res.ok) return;
      data.routine = await res.json();
      renderResult(data, false);
    } catch { /* keep the current plan */ }
  }

  /* ---------------- reminder (.ics) ---------------- */
  function downloadReminder() {
    const d = new Date(Date.now() + RESCAN_DAYS * 864e5);
    d.setHours(9, 0, 0, 0);
    const pad = (n) => String(n).padStart(2, "0");
    const stamp = (x) => `${x.getUTCFullYear()}${pad(x.getUTCMonth() + 1)}${pad(x.getUTCDate())}T${pad(x.getUTCHours())}${pad(x.getUTCMinutes())}00Z`;
    const end = new Date(d.getTime() + 15 * 60000);
    const ics = [
      "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//TwachaAI//EN", "BEGIN:VEVENT",
      `UID:${Date.now()}@twacha.ai`, `DTSTAMP:${stamp(new Date())}`, `DTSTART:${stamp(d)}`, `DTEND:${stamp(end)}`,
      `SUMMARY:${t("reminderTitle")}`, `DESCRIPTION:${location.origin}`, "END:VEVENT", "END:VCALENDAR",
    ].join("\r\n");
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([ics], { type: "text/calendar" }));
    a.download = "twacha-rescan.ics";
    a.click();
  }

  /* ---------------- wire up ---------------- */
  function init() {
    $("fileInput").addEventListener("change", (e) => onFile(e.target.files[0]));
    const dz = $("dropzone");
    dz.addEventListener("dragover", (e) => { e.preventDefault(); dz.classList.add("drag"); });
    dz.addEventListener("dragleave", () => dz.classList.remove("drag"));
    dz.addEventListener("drop", (e) => { e.preventDefault(); dz.classList.remove("drag"); onFile(e.dataTransfer.files[0]); });
    dz.addEventListener("click", () => { if (!state.stream) $("fileInput").click(); });
    $("cameraBtn").addEventListener("click", toggleCamera);
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) $("cameraBtn").hidden = true;
    $("snapBtn").addEventListener("click", snap);
    $("scanForm").addEventListener("submit", analyze);
    $("langToggle").addEventListener("click", () => {
      state.lang = state.lang === "en" ? "hi" : "en";
      localStorage.setItem("twacha.lang", state.lang);
      applyLang();
    });
    document.querySelectorAll(".seg-btn").forEach((b) => b.addEventListener("click", () => { state.tab = b.dataset.tab; renderRoutine(); }));
    $("replanBudget").addEventListener("click", (e) => {
      const b = e.target.closest("[data-budget]");
      if (b) replan(Number(b.dataset.budget), $("replanClimate").value);
    });
    $("replanClimate").addEventListener("change", (e) => replan(state.result.routine.budget, e.target.value));
    $("reportList").addEventListener("click", (e) => {
      const b = e.target.closest("[data-mask]");
      if (!b) return;
      $("maskImg").src = b.dataset.mask;
      $("maskViewer").hidden = false;
      $("maskViewer").scrollIntoView({ behavior: "smooth", block: "center" });
    });
    $("maskClose").addEventListener("click", () => ($("maskViewer").hidden = true));
    $("reminderBtn").addEventListener("click", downloadReminder);
    $("clearHistoryBtn").addEventListener("click", () => {
      localStorage.removeItem(HISTORY_KEY);
      state.previous = null;
      $("progressSub").textContent = t("cleared");
      $("progressList").innerHTML = "";
    });
    $("rescanBtn").addEventListener("click", () => show("scanView"));

    fetch("/api/config").then((r) => r.json()).then((cfg) => {
      state.config = cfg;
      setModeBadge();
      const acts = cfg.actions && (cfg.quality === "hd" ? cfg.actions.hd : cfg.actions.sd);
      if (acts) $("actionsUsed").innerHTML = acts.map((a) => `<code>${esc(a)}</code>`).join("");
    }).catch(() => {});
    applyLang();
  }

  document.addEventListener("DOMContentLoaded", init);
})();
