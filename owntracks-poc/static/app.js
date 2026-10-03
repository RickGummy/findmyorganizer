const POLL_MS = 2000;

const map = L.map("map").setView([20, 0], 2);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution: "&copy; OpenStreetMap contributors",
}).addTo(map);

let marker = null;
let circle = null;
let lastKey = null;

const $ = (id) => document.getElementById(id);

function fmtPhoneTime(tst) {
  if (tst == null) return "—";
  return `${new Date(tst * 1000).toLocaleString()} (tst ${tst})`;
}

function setStatus(text, cls) {
  const el = $("status");
  el.textContent = text;
  el.className = cls;
}

function render(loc) {
  $("lat").textContent = loc.latitude;
  $("lon").textContent = loc.longitude;
  $("acc").textContent = loc.accuracy != null ? `${loc.accuracy} m` : "—";
  $("tst").textContent = fmtPhoneTime(loc.timestamp);
  $("recv").textContent = new Date(loc.receivedAt).toLocaleString();
  $("batt").textContent = loc.battery != null ? `${loc.battery}%` : "—";
  setStatus("Location received", "received");

  const key = `${loc.latitude},${loc.longitude},${loc.accuracy},${loc.receivedAt}`;
  if (key === lastKey) return;
  const firstFix = lastKey === null;
  lastKey = key;

  const latlng = [loc.latitude, loc.longitude];

  if (!marker) {
    marker = L.marker(latlng).addTo(map).bindPopup("My iPhone — latest OwnTracks location");
  } else {
    marker.setLatLng(latlng);
  }

  if (loc.accuracy != null && loc.accuracy > 0) {
    if (!circle) {
      circle = L.circle(latlng, { radius: loc.accuracy, color: "#1e88e5", fillOpacity: 0.15, weight: 1 }).addTo(map);
    } else {
      circle.setLatLng(latlng).setRadius(loc.accuracy);
    }
  } else if (circle) {
    map.removeLayer(circle);
    circle = null;
  }

  if (firstFix) {
    map.setView(latlng, 17);
    marker.openPopup();
  } else {
    map.panTo(latlng);
  }
}

async function poll() {
  try {
    const res = await fetch("/api/location", { cache: "no-store" });
    const data = await res.json();
    if (data.success) {
      render(data);
    } else {
      setStatus("Waiting for OwnTracks...", "waiting");
    }
  } catch (err) {
    setStatus(`Cannot reach server: ${err.message}`, "error");
  }
}

poll();
setInterval(poll, POLL_MS);
