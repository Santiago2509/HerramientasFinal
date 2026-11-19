"use strict";

const byId = id => document.getElementById(id);
const integer = new Intl.NumberFormat("es-CO");
const dollars = new Intl.NumberFormat("es-CO", {
  style: "currency", currency: "USD", currencyDisplay: "narrowSymbol", maximumFractionDigits: 0,
});
const decimal = new Intl.NumberFormat("es-CO", { maximumFractionDigits: 3 });
const percent = new Intl.NumberFormat("es-CO", { style: "percent", maximumFractionDigits: 2 });
const compact = new Intl.NumberFormat("es-CO", { notation: "compact", maximumFractionDigits: 1 });
const scientific = new Intl.NumberFormat("es-CO", { notation: "scientific", maximumFractionDigits: 2 });
const avg = (sum, n) => n ? sum / n : null;
const money = value => value === null ? "—" : dollars.format(value);
const filters = Object.fromEntries(["zip", "beds", "water", "price"].map(id => [id, byId(id)]));
let sales = [];
let filtered = [];
let buildYears = [];
let metadata;
let map;
let markerLayer;

async function readJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(url + " devolvió HTTP " + response.status);
  return response.json();
}

function addOption(select, text, value) {
  select.add(new Option(text, value));
}

function empty(message = "Sin ventas en esta selección.") {
  const element = document.createElement("p");
  element.className = "empty";
  element.textContent = message;
  return element;
}

function grouped(rows, key) {
  const groups = new Map();
  for (const row of rows) {
    const name = key(row);
    if (!groups.has(name)) groups.set(name, { name, count: 0, price: 0, lat: 0, lon: 0 });
    const group = groups.get(name);
    group.count++;
    group.price += row.price;
    group.lat += row.lat;
    group.lon += row.long;
  }
  return [...groups.values()].map(group => ({
    name: group.name,
    count: group.count,
    mean: group.price / group.count,
    lat: group.lat / group.count,
    lon: group.lon / group.count,
  }));
}

function track(value, max) {
  const outer = document.createElement("div");
  const bar = document.createElement("span");
  outer.className = "track";
  outer.setAttribute("aria-hidden", "true");
  bar.style.width = 100 * value / Math.max(1, max) + "%";
  outer.append(bar);
  return outer;
}

function span(text, className = "") {
  const node = document.createElement("span");
  node.textContent = text;
  node.className = className;
  return node;
}

function drawBars(container, entries, formatter, showCount = false) {
  if (!entries.some(entry => entry.count)) {
    container.replaceChildren(empty());
    return;
  }
  const maximum = Math.max(...entries.map(entry => entry.value));
  container.replaceChildren(...entries.map(entry => {
    const row = document.createElement("div");
    row.className = "bar-line";
    const label = span(entry.label);
    if (showCount) {
      label.append(document.createElement("br"));
      const count = document.createElement("small");
      count.textContent = integer.format(entry.count) + (entry.count === 1 ? " venta" : " ventas");
      label.append(count);
    }
    row.append(label, track(entry.value, maximum), span(entry.count || !showCount ? formatter(entry.value) : "—", "number"));
    return row;
  }));
}

function updateRanking(groups) {
  const list = byId("ranking");
  const top = groups.slice(0, 10);
  if (!top.length) {
    const item = document.createElement("li");
    item.append(empty());
    list.replaceChildren(item);
    return;
  }
  list.replaceChildren(...top.map(group => {
    const item = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    button.setAttribute("aria-pressed", String(filters.zip.value === group.name));
    button.setAttribute("aria-label", "Código " + group.name + ", " + money(group.mean)
      + ", " + integer.format(group.count) + " ventas");
    button.append(span(group.name), track(group.mean, top[0].mean), span(money(group.mean), "number"));
    button.addEventListener("click", () => {
      filters.zip.value = filters.zip.value === group.name ? "" : group.name;
      render();
      list.querySelector('[aria-pressed="true"]')?.focus();
    });
    item.append(button);
    return item;
  }));
}

function initializeMap(boundary) {
  map = L.map("map", { scrollWheelZoom: false, minZoom: 8, maxZoom: 15 })
    .setView([47.49, -122.16], 9);
  map.attributionControl.setPrefix(false);
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  }).addTo(map);
  if (boundary) L.geoJSON(boundary, {
    interactive: false,
    style: { color: "#407662", weight: 1.5, fillColor: "#b5d3bd", fillOpacity: 0.18 },
    attribution: "Límites: U.S. Census Bureau",
  }).addTo(map);
  markerLayer = L.layerGroup().addTo(map);
  new ResizeObserver(() => map.invalidateSize({ pan: false })).observe(byId("map"));
}

function updateMap(groups) {
  markerLayer.clearLayers();
  const legend = byId("map-legend");
  if (!groups.length) {
    legend.replaceChildren(empty());
    return;
  }
  const low = groups.at(-1).mean;
  const high = groups[0].mean;
  const scale = span("", "map-scale");
  scale.setAttribute("aria-hidden", "true");
  legend.replaceChildren(span(money(low)), scale, span(money(high)));
  for (const group of [...groups].reverse()) {
    const scalePosition = high === low ? 0.7 : (group.mean - low) / (high - low);
    const diameter = Math.min(28, 8 + Math.sqrt(group.count) * 0.7);
    const color = [138, 196, 162].map((channel, i) =>
      Math.round(channel + ([21, 61, 55][i] - channel) * scalePosition)
    );
    const dot = document.createElement("span");
    dot.style.cssText = "display:block;width:100%;height:100%;border-radius:100%;border:2px solid white;"
      + "box-shadow:0 0 0 1px #30574d;background:rgb(" + color.join(",") + ")";
    const description = "Código postal " + group.name + " · " + money(group.mean);
    const icon = L.divIcon({ html: dot, className: "zip-marker", iconSize: [diameter, diameter] });
    const marker = L.marker([group.lat, group.lon], { icon, title: description });
    const popup = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = description;
    popup.append(title, document.createElement("br"), integer.format(group.count) + " ventas");
    marker.bindPopup(popup).addTo(markerLayer);
    marker.getElement().setAttribute("aria-label", description);
  }
}

function pearson(rows) {
  const n = rows.length;
  if (n < 2) return null;
  let sx = 0, sy = 0, xx = 0, yy = 0, xy = 0;
  for (const { living_m2: x, price: y } of rows) {
    sx += x;
    sy += y;
    xx += x * x;
    yy += y * y;
    xy += x * y;
  }
  const xVariance = n * xx - sx * sx;
  const yVariance = n * yy - sy * sy;
  if (xVariance <= 0 || yVariance <= 0) return null;
  return (n * xy - sx * sy) / Math.sqrt(xVariance * yVariance);
}

function drawCanvas(canvas, series, chart) {
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  if (!width || !height) return;
  const pixelRatio = window.devicePixelRatio || 1;
  canvas.width = width * pixelRatio;
  canvas.height = height * pixelRatio;
  const ctx = canvas.getContext("2d");
  ctx.scale(pixelRatio, pixelRatio);
  ctx.font = "14px system-ui";
  ctx.fillStyle = "#4c6359";
  if (!series.length) {
    ctx.fillText("Sin ventas en esta selección.", 12, 30);
    return;
  }
  const padding = { left: 64, right: 14, top: 12, bottom: 44 };
  const plotW = width - padding.left - padding.right;
  const plotH = height - padding.top - padding.bottom;
  const startX = chart === "trend" ? Math.min(...series.map(p => p.x)) : 0;
  const endX = Math.max(startX + 1, ...series.map(p => p.x));
  const maxY = Math.max(...series.map(p => p.y));
  const quantum = 10 ** Math.floor(Math.log10(maxY));
  const endY = Math.ceil(maxY / quantum) * quantum;
  const xAt = x => padding.left + (x - startX) / (endX - startX) * plotW;
  const yAt = y => padding.top + (1 - y / endY) * plotH;
  for (let tick = 0; tick <= 4; tick++) {
    const y = endY * tick / 4;
    ctx.beginPath();
    ctx.strokeStyle = "#dbe5df";
    ctx.moveTo(padding.left, yAt(y));
    ctx.lineTo(width - padding.right, yAt(y));
    ctx.stroke();
    ctx.textAlign = "right";
    ctx.fillText("$" + compact.format(y), padding.left - 5, yAt(y) + 4);
    const x = startX + (endX - startX) * tick / 4;
    ctx.textAlign = "center";
    ctx.fillText(String(Math.round(x)), xAt(x) - (tick === 4 ? 8 : 0), height - 24);
  }
  ctx.fillText(chart === "trend" ? "Año de construcción" : "Superficie habitable (m²)", width / 2 + 15, height - 4);
  if (chart === "trend") {
    ctx.beginPath();
    ctx.strokeStyle = "#297858";
    ctx.lineWidth = 2;
    for (const { x, y } of series) ctx.lineTo(xAt(x), yAt(y));
    ctx.stroke();
    ctx.fillStyle = "#1c654e";
  } else {
    ctx.fillStyle = "rgba(33, 112, 76, .42)";
  }
  for (const { x, y } of series) {
    ctx.beginPath();
    ctx.arc(xAt(x), yAt(y), chart === "trend" ? 2.3 : 1.9, 0, 2 * Math.PI);
    ctx.fill();
  }
}

function updatePlots() {
  const step = Math.max(1, Math.ceil(filtered.length / 2800));
  // Mantiene los extremos aunque no coincidan con el intervalo de muestreo.
  const extreme = filtered.reduce((max, row) => !max || row.price > max.price ? row : max, null);
  const widest = filtered.reduce((max, row) => !max || row.living_m2 > max.living_m2 ? row : max, null);
  const points = new Set(filtered.filter((_, index) => index % step === 0));
  if (extreme) points.add(extreme);
  if (widest) points.add(widest);
  drawCanvas(byId("scatter"), [...points].map(row => ({ x: row.living_m2, y: row.price })), "scatter");
  drawCanvas(byId("trend"), buildYears, "trend");
}

function render() {
  filtered = sales.filter(row =>
    (!filters.zip.value || row.zipcode === filters.zip.value)
    && (!filters.beds.value || (filters.beds.value === "6+" ? row.bedrooms >= 6 : row.bedrooms === Number(filters.beds.value)))
    && (!filters.water.value || row.waterfront === Number(filters.water.value))
    && (!filters.price.value || row.band === Number(filters.price.value))
  );
  let totalPrice = 0, totalUnit = 0, waterfront = 0;
  const bandCounts = Array(metadata.priceBands.length).fill(0);
  for (const row of filtered) {
    totalPrice += row.price;
    totalUnit += row.price / row.living_m2;
    waterfront += row.waterfront;
    bandCounts[row.band]++;
  }
  const n = filtered.length;
  byId("result-status").textContent = integer.format(n) + " de " + integer.format(metadata.sales) + " ventas";
  byId("total").textContent = integer.format(n);
  byId("mean").textContent = money(avg(totalPrice, n));
  byId("unit").textContent = money(avg(totalUnit, n));
  byId("water-count").textContent = integer.format(waterfront);
  byId("water-share").textContent = n ? percent.format(waterfront / n) + " de las ventas" : "de las ventas";

  const zips = grouped(filtered, row => row.zipcode).sort((a, b) =>
    b.mean - a.mean || a.name.localeCompare(b.name)
  );
  updateRanking(zips);
  if (markerLayer) updateMap(zips);

  drawBars(byId("bands"), metadata.priceBands.map((band, index) => ({
    label: band.label, value: bandCounts[index], count: bandCounts[index],
  })), n => integer.format(n));
  const r = pearson(filtered);
  byId("correlation").textContent = r === null ? "Se necesitan ventas con valores distintos para calcular Pearson."
    : "Pearson r = " + decimal.format(r) + " · " + integer.format(n) + " ventas"
      + (n > 2800 ? " · El gráfico muestra una muestra." : ".");
  buildYears = grouped(filtered, row => row.yr_built).sort((a, b) => a.name - b.name)
    .map(group => ({ x: group.name, y: group.mean }));
  updatePlots();

  const withLabels = (groups, labels) => labels.map((label, index) => {
    const group = groups.find(item => item.name === index);
    return { label, value: group?.mean ?? 0, count: group?.count ?? 0 };
  });
  drawBars(byId("water-prices"), withLabels(grouped(filtered, row => row.waterfront),
    ["Sin frente al agua", "Frente al agua"]), money, true);
  drawBars(byId("bed-prices"), withLabels(grouped(filtered, row => Math.min(6, row.bedrooms)),
    ["0", "1", "2", "3", "4", "5", "6+"]), money, true);
  drawBars(byId("bath-prices"), withLabels(grouped(filtered, row => Math.min(5, Math.floor(row.bathrooms))),
    ["0", "1", "2", "3", "4", "5+"]), money, true);
}

function table(headers, rows) {
  const result = document.createElement("table");
  const header = result.createTHead().insertRow();
  for (const text of headers) {
    const cell = document.createElement("th");
    cell.scope = "col";
    cell.textContent = text;
    header.append(cell);
  }
  const body = result.createTBody();
  for (const row of rows) {
    const cells = body.insertRow();
    for (const text of row) cells.insertCell().textContent = text;
  }
  return result;
}

function paragraph(text) {
  const node = document.createElement("p");
  node.className = "stat-note";
  node.textContent = text;
  return node;
}

function showStatistics({ anova, model }) {
  const rejected = anova.welch.p < anova.alpha;
  byId("anova").replaceChildren(
    table(["Habitaciones", "Propiedades", "Media (USD)", "Mediana (USD)"], anova.groups.map(group =>
      [group.bedrooms, integer.format(group.count), money(group.mean), money(group.median)])),
    paragraph("Welch F = " + decimal.format(anova.welch.statistic) + " · p = " + scientific.format(anova.welch.p)
      + " · Levene p = " + scientific.format(anova.levene.p)),
    paragraph(rejected ? "Las medias difieren entre al menos dos grupos. El resultado expresa asociación."
      : "La prueba no detectó diferencias entre las medias al 5 %."),
  );
  const metrics = table(["Modelo", "MAE (USD)", "RMSE (USD)", "R²"], model.metrics.map(item =>
    [item.name, money(item.mae), money(item.rmse), decimal.format(item.r2)]));
  for (const row of metrics.tBodies[0].rows) {
    if (row.cells[0].textContent === model.bestByMae) row.className = "model-best";
  }
  byId("model").replaceChildren(metrics, paragraph(integer.format(model.testRows)
    + " ventas evaluadas. MAE es el error absoluto medio en dólares. La referencia predice la mediana de entrenamiento."));
}

async function initialize() {
  document.querySelectorAll(".sidebar nav a").forEach(link => link.addEventListener("click", () => {
    document.querySelector(".sidebar nav [aria-current]")?.removeAttribute("aria-current");
    link.setAttribute("aria-current", "location");
  }));

  const stats = readJson("analisis.json").then(showStatistics).catch(error => {
    console.error(error);
    for (const id of ["anova", "model"]) byId(id).replaceChildren(empty("No se pudieron cargar los resultados."));
  });
  const boundary = readJson("assets/king-county.geojson").catch(error => {
    console.warn(error);
    return null;
  });
  try {
    const data = await readJson("ventas.json");
    metadata = data.metadata;
    sales = data.rows.map(row => {
      const sale = Object.fromEntries(data.fields.map((key, i) => [key, row[i]]));
      sale.band = metadata.priceBands.findLastIndex(band => sale.price >= band.min);
      return sale;
    });
    const zipcodes = [...new Set(sales.map(sale => sale.zipcode))].sort();
    zipcodes.forEach(code => addOption(filters.zip, code, code));
    metadata.priceBands.forEach((band, index) => addOption(filters.price, band.label, index));
    if (window.L) initializeMap(await boundary);
    else byId("map").append(empty("El mapa no se pudo cargar. Los precios están en el listado."));
    const form = document.querySelector(".filters");
    form.addEventListener("change", render);
    form.addEventListener("reset", () => requestAnimationFrame(render));
    render();
    const resize = new ResizeObserver(updatePlots);
    for (const id of ["scatter", "trend"]) resize.observe(byId(id));
  } catch (error) {
    console.error(error);
    byId("result-status").textContent = "No se pudieron cargar las ventas. Recarga la página e inténtalo de nuevo.";
  }
  await stats;
}

initialize();
