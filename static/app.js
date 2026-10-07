const $ = (id) => document.getElementById(id);
let sample = "corner",
  photo = null,
  project = null,
  selected = 0,
  objectURL = null,
  busy = false;
const settingIds = [
  "length",
  "height",
  "min_length",
  "min_height",
  "depth",
  "thickness",
];
async function api(url, options = {}) {
  const res = await fetch(url, options);
  if (!res.ok) {
    let body;
    try {
      body = await res.json();
    } catch {
      body = { detail: "Request failed. Please try again." };
    }
    throw new Error(
      typeof body.detail === "string"
        ? body.detail
        : JSON.stringify(body.detail),
    );
  }
  return res.json();
}
function notice(title, message, error = false) {
  $("notice").classList.toggle("error", error);
  $("notice").replaceChildren();
  const icon = document.createElement("span");
  icon.textContent = error ? "!" : "↳";
  const div = document.createElement("div");
  const strong = document.createElement("strong");
  strong.textContent = title;
  const p = document.createElement("p");
  p.textContent = message;
  div.append(strong, p);
  $("notice").append(icon, div);
}
function reset() {
  project = null;
  $("canvas-label").textContent = "A cut is a new constraint.";
  $("timing").textContent = "Calibrated in millimetres";
  $("results").hidden = true;
  $("accepted").hidden = true;
  $("verification").hidden = true;
  $("trace-section").hidden = true;
  $("verify-result").textContent = "";
  $("verify-photo").value = "";
  $("step2").classList.remove("active");
  $("step3").classList.remove("active");
}
function setPreview(url) {
  $("preview").src = url;
  $("preview").alt = "Current material photograph or labeled synthetic inspection evidence";
}
document.querySelectorAll(".sample").forEach((btn) =>
  btn.addEventListener("click", () => {
    if (busy) return;
    reset();
    photo = null;
    sample = btn.dataset.sample;
    $("photo").value = "";
    $("filename").textContent = "Add your photograph";
    document
      .querySelectorAll(".sample")
      .forEach((b) => b.classList.toggle("selected", b === btn));
    setPreview("/api/samples/" + sample);
    $("source").textContent = "SYNTHETIC SAMPLE";
    notice(
      "Generated sample selected.",
      "This image is synthetic. It exercises the real OpenCV pipeline but is not evidence of physical accuracy.",
    );
  }),
);
$("photo").addEventListener("change", (e) => {
  if (busy) return;
  const file = e.target.files[0];
  if (!file) return;
  if (file.size > 10 * 1024 * 1024) {
    notice(
      "Image is too large.",
      "Please choose a PNG or JPEG below 10 MB.",
      true,
    );
    return;
  }
  reset();
  photo = file;
  sample = null;
  document
    .querySelectorAll(".sample")
    .forEach((b) => b.classList.remove("selected"));
  $("filename").textContent = file.name;
  $("source").textContent = "YOUR PHOTOGRAPH";
  if (objectURL) URL.revokeObjectURL(objectURL);
  objectURL = URL.createObjectURL(file);
  setPreview(objectURL);
  notice(
    "Photograph ready.",
    "Keep the blank flat and aligned with the mat. All four markers and the entire material boundary must be visible.",
  );
});
settingIds.forEach((id) =>
  $(id).addEventListener("input", () => {
    if (project) {
      reset();
      notice(
        "Constraints changed.",
        "Run a new inspection before accepting a plan.",
      );
    }
  }),
);
function trace() {
  const list = $("trace");
  list.replaceChildren();
  project.trace.forEach((item) => {
    const li = document.createElement("li"),
      strong = document.createElement("strong");
    strong.textContent = item.tool.replaceAll("_", " ");
    li.append(strong, document.createTextNode(item.result));
    list.append(li);
  });
  $("trace-section").hidden = false;
}
function showOption(i) {
  selected = i;
  setPreview(project.options[i].overlay);
  $("canvas-label").textContent =
    `Option ${i + 1} · ${project.options[i].length} × ${project.options[i].height} mm`;
  document
    .querySelectorAll(".option")
    .forEach((el, n) => el.classList.toggle("selected", i === n));
}
function renderOptions() {
  const parent = $("options");
  parent.replaceChildren();
  project.options.forEach((opt, i) => {
    const card = document.createElement("article");
    card.className = "option";
    card.innerHTML = `<div class="option-head"><span>RECOVERY ${String(i + 1).padStart(2, "0")}</span><span>${i === 0 ? "MOST AREA RETAINED" : "ALTERNATIVE"}</span></div><h3>${opt.length} × ${opt.height} <small>mm</small></h3><div class="meter"><span style="width:${opt.retained_percent}%"></span></div><p><strong>${opt.retained_percent}%</strong> of the original panel area retained.<br>Companion: ${opt.companion.length} × ${opt.companion.height} mm<br>Both slots: ${opt.companion.slot_width} mm wide × ${opt.companion.slot_depth} mm deep</p><div class="option-actions"><button class="secondary" data-preview="${i}">Preview</button><button class="primary" data-accept="${i}">Accept this plan ↗</button></div>`;
    parent.append(card);
  });
  parent
    .querySelectorAll("[data-preview]")
    .forEach((b) => (b.onclick = () => showOption(Number(b.dataset.preview))));
  parent
    .querySelectorAll("[data-accept]")
    .forEach((b) => (b.onclick = () => accept(Number(b.dataset.accept))));
  $("results").hidden = false;
  showOption(0);
}
function setBusy(value) {
  busy = value;
  $("inspect").disabled = value;
  $("photo").disabled = value;
  document.querySelectorAll(".sample").forEach((b) => (b.disabled = value));
  settingIds.forEach((id) => ($(id).disabled = value));
}
$("inspect").onclick = async () => {
  reset();
  setBusy(true);
  $("inspect").textContent = "Measuring your material…";
  notice(
    "Inspecting the actual outline.",
    "Checking calibration, measuring material, and searching valid recovery dimensions.",
  );
  try {
    const settings = Object.fromEntries(
      settingIds.map((id) => [id, Number($(id).value)]),
    );
    const body = new FormData();
    body.append("settings", JSON.stringify(settings));
    if (photo) body.append("file", photo);
    else body.append("demo", sample || "corner");
    project = await api("/api/inspect", { method: "POST", body });
    $("timing").textContent =
      `${Math.round(project.elapsed_ms)} ms · OpenCV ${project.opencv}`;
    $("source").textContent =
      project.source === "synthetic fixture"
        ? "SYNTHETIC SAMPLE"
        : "YOUR PHOTOGRAPH";
    if (project.image) setPreview(project.image);
    trace();
    if (project.status === "review") {
      renderOptions();
      $("step2").classList.add("active");
      notice("There is a way forward.", project.message);
    } else {
      notice(
        project.status === "recapture"
          ? "One more photograph, please."
          : "This panel needs replacing.",
        project.message,
        true,
      );
    }
  } catch (e) {
    notice("Inspection could not finish.", e.message, true);
  } finally {
    setBusy(false);
    $("inspect").innerHTML = "Find my second cut <span>↗</span>";
  }
};
async function accept(i) {
  try {
    project = await api(`/api/projects/${project.id}/approve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ option: i }),
    });
    showOption(i);
    $("template").href = `/api/projects/${project.id}/template.svg`;
    $("report").href = `/api/projects/${project.id}/report.json`;
    $("accepted").hidden = false;
    $("verification").hidden = false;
    $("verify-result").textContent = "";
    $("step3").classList.add("active");
    trace();
    notice(
      "Repair plan accepted.",
      "The template includes both compatible panels. Measure material thickness and test the slot fit before cutting your salvaged piece.",
    );
    $("accepted").scrollIntoView({ behavior: "smooth", block: "center" });
  } catch (e) {
    notice("Could not accept the plan.", e.message, true);
  }
}
async function verify(file) {
  if (!project) return;
  const pid = project.id;
  const body = new FormData();
  if (file) body.append("file", file);
  else body.append("demo", "true");
  $("verify-result").textContent =
    "Comparing the new capture with your accepted plan…";
  $("verify-demo").disabled = true;
  try {
    const result = await api(`/api/projects/${pid}/verify`, {
      method: "POST",
      body,
    });
    $("verify-result").textContent =
      `${file ? "Photo check" : "Synthetic check"}: ${result.message}`;
    if (result.image) setPreview(result.image);
    $("source").textContent = file ? "YOUR PHOTOGRAPH" : "SYNTHETIC SAMPLE";
    $("canvas-label").textContent =
      result.status === "geometry_matches"
        ? "Visible geometry matches the plan."
        : "Review the new capture.";
    const report = await api(`/api/projects/${pid}/report.json`);
    project.trace = report.trace;
    project.verification = report.verification;
    trace();
  } catch (e) {
    $("verify-result").textContent = e.message;
  } finally {
    $("verify-demo").disabled = false;
  }
}
$("verify-demo").onclick = () => verify(null);
$("verify-photo").onchange = (e) => {
  if (e.target.files[0]) verify(e.target.files[0]);
};
api("/api/health")
  .then((v) => {
    $("runtime").textContent = `OpenCV ${v.opencv} · ${v.deployment}`;
    if (!v.opencv5)
      notice(
        "OpenCV version requirement unmet.",
        "This build is not running OpenCV 5.",
        true,
      );
  })
  .catch(() => {
    $("runtime").textContent = "Vision engine unavailable";
    notice(
      "Backend unavailable.",
      "Start the SecondCut server and refresh this page.",
      true,
    );
  });
