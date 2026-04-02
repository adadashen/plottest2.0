const uploadForm = document.getElementById("upload-form");
const uploadMessage = document.getElementById("upload-message");
const datasetFileInput = document.getElementById("dataset-file");
const sheetRow = document.getElementById("sheet-row");
const sheetNameSelect = document.getElementById("sheet-name");
const previewMessage = document.getElementById("preview-message");
const previewTableHead = document.querySelector("#preview-table thead");
const previewTableBody = document.querySelector("#preview-table tbody");
const refreshDatasetsBtn = document.getElementById("refresh-datasets");
const datasetsTableBody = document.querySelector("#datasets-table tbody");
const currentDatasetMessage = document.getElementById("current-dataset-message");
const timeColumnSelect = document.getElementById("time-column");
const leftYGroupsEl = document.getElementById("left-y-groups");
const rightYGroupsEl = document.getElementById("right-y-groups");
const addLeftGroupBtn = document.getElementById("btn-add-left-group");
const addRightGroupBtn = document.getElementById("btn-add-right-group");
const plotMessage = document.getElementById("plot-message");
const plotFrame = document.getElementById("plot-frame");
const seriesColorSettings = document.getElementById("series-color-settings");
let currentDatasetId = null;
let pendingFileNeedsUpload = false;
let currentColumns = [];
const MAX_Y_GROUPS = 10;
const DEFAULT_SERIES_COLORS = [
    "#d62728",
    "#1f77b4",
    "#2ca02c",
    "#9467bd",
    "#ff7f0e",
    "#17becf",
    "#e377c2",
    "#8c564b",
    "#bcbd22",
    "#7f7f7f",
];
const seriesColorOverrides = {};

function getYGroupSelects(groupsEl) {
    return Array.from(groupsEl.querySelectorAll("select[data-y-group]"));
}

function getYGroupValues(groupsEl) {
    return getYGroupSelects(groupsEl)
        .map((sel) => sel.value)
        .filter((v) => v && String(v).trim() !== "");
}

function getAllSelectedSeriesColumns() {
    const ordered = [...getYGroupValues(leftYGroupsEl), ...getYGroupValues(rightYGroupsEl)];
    const seen = new Set();
    return ordered.filter((col) => {
        if (seen.has(col)) return false;
        seen.add(col);
        return true;
    });
}

function getDefaultSeriesColor(column, index) {
    return seriesColorOverrides[column] || DEFAULT_SERIES_COLORS[index % DEFAULT_SERIES_COLORS.length];
}

function buildSeriesColorMap() {
    const cols = getAllSelectedSeriesColumns();
    const map = {};
    cols.forEach((col, idx) => {
        map[col] = getDefaultSeriesColor(col, idx);
    });
    return map;
}

function renderSeriesColorSettings() {
    const cols = getAllSelectedSeriesColumns();
    if (!cols.length) {
        seriesColorSettings.innerHTML = '<p class="hint" style="margin:0;">请先选择左右轴曲线列</p>';
        return;
    }
    const html = cols
        .map((col, idx) => {
            const color = getDefaultSeriesColor(col, idx);
            return `
                <div class="series-color-item">
                    <span>${col}</span>
                    <input type="color" data-series-color="${col}" value="${color}" />
                </div>
            `;
        })
        .join("");
    seriesColorSettings.innerHTML = html;
    for (const input of seriesColorSettings.querySelectorAll('input[type="color"][data-series-color]')) {
        input.addEventListener("input", (e) => {
            const col = e.target.getAttribute("data-series-color");
            seriesColorOverrides[col] = e.target.value;
        });
    }
}

function buildPlotQueryParams(timeColumn, leftYColumns, rightYColumns) {
    const params = new URLSearchParams();
    params.set("time_column", timeColumn);
    for (const col of leftYColumns) {
        params.append("left_y_columns", col);
    }
    for (const col of rightYColumns) {
        params.append("right_y_columns", col);
    }

    const chartTitle = document.getElementById("fmt-title").value.trim();
    if (chartTitle) params.set("chart_title", chartTitle);
    const xTitle = document.getElementById("fmt-x-title").value.trim();
    if (xTitle) params.set("x_title", xTitle);
    const yLeftTitle = document.getElementById("fmt-y-left-title").value.trim();
    if (yLeftTitle) params.set("y_left_title", yLeftTitle);
    const yRightTitle = document.getElementById("fmt-y-right-title").value.trim();
    if (yRightTitle) params.set("y_right_title", yRightTitle);

    const xMin = document.getElementById("fmt-x-min").value.trim();
    const xMax = document.getElementById("fmt-x-max").value.trim();
    if (xMin && xMax) {
        params.set("x_min", xMin);
        params.set("x_max", xMax);
    } else if (xMin || xMax) {
        throw new Error("时间轴下限与上限需同时填写或同时留空");
    }

    const xDtick = document.getElementById("fmt-x-dtick").value.trim();
    if (xDtick !== "") {
        const v = parseFloat(xDtick);
        if (Number.isNaN(v) || v <= 0) {
            throw new Error("时间刻度间隔（小时）须为正数");
        }
        params.set("x_dtick_hours", String(v));
    }

    const ylMin = document.getElementById("fmt-y-left-min").value.trim();
    const ylMax = document.getElementById("fmt-y-left-max").value.trim();
    if (ylMin !== "" && ylMax !== "") {
        params.set("y_left_min", ylMin);
        params.set("y_left_max", ylMax);
    } else if (ylMin || ylMax) {
        throw new Error("左 Y 轴下限与上限需同时填写或同时留空");
    }

    const ylDtick = document.getElementById("fmt-y-left-dtick").value.trim();
    if (ylDtick !== "") {
        const v = parseFloat(ylDtick);
        if (Number.isNaN(v) || v <= 0) {
            throw new Error("左 Y 轴刻度间隔须为正数");
        }
        params.set("y_left_dtick", String(v));
    }

    const yrMin = document.getElementById("fmt-y-right-min").value.trim();
    const yrMax = document.getElementById("fmt-y-right-max").value.trim();
    if (yrMin !== "" && yrMax !== "") {
        params.set("y_right_min", yrMin);
        params.set("y_right_max", yrMax);
    } else if (yrMin || yrMax) {
        throw new Error("右 Y 轴下限与上限需同时填写或同时留空");
    }

    const yrDtick = document.getElementById("fmt-y-right-dtick").value.trim();
    if (yrDtick !== "") {
        const v = parseFloat(yrDtick);
        if (Number.isNaN(v) || v <= 0) {
            throw new Error("右 Y 轴刻度间隔须为正数");
        }
        params.set("y_right_dtick", String(v));
    }

    params.set("series_colors_json", JSON.stringify(buildSeriesColorMap()));
    return params;
}

function resetChartFormatToDefaults() {
    document.getElementById("fmt-title").value = "";
    document.getElementById("fmt-x-title").value = "";
    document.getElementById("fmt-y-left-title").value = "";
    document.getElementById("fmt-y-right-title").value = "";
    document.getElementById("fmt-x-min").value = "";
    document.getElementById("fmt-x-max").value = "";
    document.getElementById("fmt-x-dtick").value = "";
    document.getElementById("fmt-y-left-min").value = "";
    document.getElementById("fmt-y-left-max").value = "";
    document.getElementById("fmt-y-left-dtick").value = "";
    document.getElementById("fmt-y-right-min").value = "";
    document.getElementById("fmt-y-right-max").value = "";
    document.getElementById("fmt-y-right-dtick").value = "";
    Object.keys(seriesColorOverrides).forEach((k) => delete seriesColorOverrides[k]);
    renderSeriesColorSettings();
}

function resetAxisFormatToDefaults(axis) {
    if (axis === "x") {
        document.getElementById("fmt-x-min").value = "";
        document.getElementById("fmt-x-max").value = "";
        document.getElementById("fmt-x-dtick").value = "";
        return;
    }
    if (axis === "left") {
        document.getElementById("fmt-y-left-min").value = "";
        document.getElementById("fmt-y-left-max").value = "";
        document.getElementById("fmt-y-left-dtick").value = "";
        return;
    }
    if (axis === "right") {
        document.getElementById("fmt-y-right-min").value = "";
        document.getElementById("fmt-y-right-max").value = "";
        document.getElementById("fmt-y-right-dtick").value = "";
    }
}

async function requestJson(url, options = {}) {
    const response = await fetch(url, options);
    const contentType = response.headers.get("content-type") || "";
    const data = contentType.includes("application/json")
        ? await response.json()
        : await response.text();
    if (!response.ok) {
        const errorMessage = data?.detail || data || `请求失败: ${response.status}`;
        throw new Error(errorMessage);
    }
    return data;
}

function setText(el, text) {
    el.textContent = text;
}

function setCurrentDataset(datasetId) {
    currentDatasetId = datasetId;
    if (currentDatasetId) {
        currentDatasetMessage.textContent = `当前数据集：ID=${currentDatasetId}`;
    } else {
        currentDatasetMessage.textContent = "当前数据集：未选择（请先上传数据）";
    }
}

function resetSheetSelector() {
    sheetNameSelect.innerHTML = "";
    sheetRow.style.display = "none";
}

function buildOptionsHtml(columns) {
    return columns.map((col) => `<option value="${col}">${col}</option>`).join("");
}

function createYGroupSelect(axis, optionsHtml) {
    const wrapper = document.createElement("div");
    wrapper.className = "y-group-row";
    const select = document.createElement("select");
    select.setAttribute("data-y-group", axis);
    select.innerHTML = optionsHtml;
    select.addEventListener("change", () => {
        resetAxisFormatToDefaults(axis === "left" ? "left" : "right");
        renderSeriesColorSettings();
    });
    wrapper.appendChild(select);
    const removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.className = "btn-danger btn-icon";
    removeBtn.textContent = "删除";
    removeBtn.addEventListener("click", () => {
        const groupsEl = axis === "left" ? leftYGroupsEl : rightYGroupsEl;
        const rows = getYGroupSelects(groupsEl);
        if (rows.length <= 1) return;
        wrapper.remove();
        updateRemoveButtonsState(groupsEl);
        renderSeriesColorSettings();
    });
    wrapper.appendChild(removeBtn);
    return { wrapper, select };
}

function updateRemoveButtonsState(groupsEl) {
    const rows = Array.from(groupsEl.querySelectorAll(".y-group-row"));
    const disable = rows.length <= 1;
    for (const row of rows) {
        const btn = row.querySelector("button.btn-danger");
        if (btn) btn.disabled = disable;
    }
}

function ensureAtLeastOneGroup(axis, groupsEl, optionsHtml, defaultValue) {
    if (getYGroupSelects(groupsEl).length > 0) return;
    const { wrapper, select } = createYGroupSelect(axis, optionsHtml);
    if (defaultValue) select.value = defaultValue;
    groupsEl.appendChild(wrapper);
    updateRemoveButtonsState(groupsEl);
}

function addYGroup(axis) {
    const groupsEl = axis === "left" ? leftYGroupsEl : rightYGroupsEl;
    const optionsHtml = buildOptionsHtml(currentColumns);
    const count = getYGroupSelects(groupsEl).length;
    if (count >= MAX_Y_GROUPS) {
        setText(plotMessage, `最多只能添加 ${MAX_Y_GROUPS} 个数据组`);
        return;
    }
    const { wrapper, select } = createYGroupSelect(axis, optionsHtml);
    // 默认选一个未被本轴占用的列
    const used = new Set(getYGroupValues(groupsEl));
    const timeCol = timeColumnSelect.value;
    const candidate = currentColumns.find((c) => c !== timeCol && !used.has(c));
    if (candidate) select.value = candidate;
    groupsEl.appendChild(wrapper);
    updateRemoveButtonsState(groupsEl);
    renderSeriesColorSettings();
}

function renderColumnSelects(columns) {
    if (!columns?.length) return;
    currentColumns = columns.slice();
    const optionsHtml = buildOptionsHtml(columns);
    timeColumnSelect.innerHTML = optionsHtml;

    const timeCandidate = columns.find((c) => /time|date|timestamp|时间/i.test(c)) || columns[0];
    timeColumnSelect.value = timeCandidate;
    // 初始化左右各 1 个数据组
    leftYGroupsEl.innerHTML = "";
    rightYGroupsEl.innerHTML = "";
    const leftDefault =
        columns.find((c) => /temp|temperature|温度/i.test(c) && c !== timeCandidate) ||
        columns.find((c) => c !== timeCandidate) ||
        "";
    const rightDefault =
        columns.find((c) => /press|pressure|压力/i.test(c) && c !== timeCandidate && c !== leftDefault) ||
        columns.find((c) => c !== timeCandidate && c !== leftDefault) ||
        "";
    ensureAtLeastOneGroup("left", leftYGroupsEl, optionsHtml, leftDefault);
    ensureAtLeastOneGroup("right", rightYGroupsEl, optionsHtml, rightDefault);
    renderSeriesColorSettings();
}

function renderPreviewTable(columns, rows) {
    previewTableHead.innerHTML = "";
    previewTableBody.innerHTML = "";
    if (!columns?.length) {
        previewMessage.textContent = "暂无预览数据";
        return;
    }
    previewTableHead.innerHTML = `<tr>${columns.map((c) => `<th>${c}</th>`).join("")}</tr>`;
    for (const row of rows) {
        const tr = document.createElement("tr");
        tr.innerHTML = columns
            .map((c) => `<td>${row[c] === null || row[c] === undefined ? "" : row[c]}</td>`)
            .join("");
        previewTableBody.appendChild(tr);
    }
}

async function previewCurrentFile() {
    const file = datasetFileInput.files?.[0];
    if (!file) {
        previewMessage.textContent = "";
        previewTableHead.innerHTML = "";
        previewTableBody.innerHTML = "";
        return;
    }
    const formData = new FormData();
    formData.append("file", file);
    if (file.name.toLowerCase().endsWith(".xlsx") && sheetNameSelect.value) {
        formData.append("sheet_name", sheetNameSelect.value);
    }
    try {
        const preview = await requestJson("/datasets/preview", { method: "POST", body: formData });
        previewMessage.textContent = "预览成功（前12行）";
        renderPreviewTable(preview.columns, preview.rows);
        renderColumnSelects(preview.columns);
    } catch (err) {
        previewMessage.textContent = `预览失败: ${err.message}`;
        previewTableHead.innerHTML = "";
        previewTableBody.innerHTML = "";
    }
}

async function detectExcelSheets() {
    const file = datasetFileInput.files?.[0];
    if (!file || !file.name.toLowerCase().endsWith(".xlsx")) {
        resetSheetSelector();
        return;
    }
    const formData = new FormData();
    formData.append("file", file);
    try {
        const result = await requestJson("/datasets/excel/sheets", {
            method: "POST",
            body: formData,
        });
        sheetNameSelect.innerHTML = "";
        for (const sheet of result.sheets) {
            const option = document.createElement("option");
            option.value = sheet;
            option.textContent = sheet;
            sheetNameSelect.appendChild(option);
        }
        sheetRow.style.display = "flex";
        setText(uploadMessage, `已识别 Excel sheet: ${result.sheets.join(", ")}`);
    } catch (err) {
        resetSheetSelector();
        setText(uploadMessage, `识别 sheet 失败: ${err.message}`);
    }
}

async function loadDatasets() {
    try {
        const datasets = await requestJson("/datasets");
        datasetsTableBody.innerHTML = "";
        if (!currentDatasetId && datasets.length > 0) {
            setCurrentDataset(datasets[0].id);
        }
        for (const item of datasets) {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${item.id}</td>
                <td>${item.name}</td>
                <td>${item.rows}</td>
                <td>${item.cols}</td>
                <td>${item.columns.join(", ")}</td>
                <td>${item.created_at}</td>
            `;
            datasetsTableBody.appendChild(tr);
        }
    } catch (err) {
        setText(uploadMessage, `加载数据集失败: ${err.message}`);
    }
}

uploadForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    uploadMessage.textContent = "正在上传...";
    const formData = new FormData(uploadForm);
    const file = datasetFileInput.files?.[0];
    if (file && file.name.toLowerCase().endsWith(".xlsx") && sheetNameSelect.value) {
        formData.set("sheet_name", sheetNameSelect.value);
    } else {
        formData.delete("sheet_name");
    }
    try {
        const result = await requestJson("/datasets/upload", { method: "POST", body: formData });
        setText(uploadMessage, `上传成功: ID=${result.id}, 行数=${result.rows}, 列数=${result.cols}`);
        setCurrentDataset(result.id);
        pendingFileNeedsUpload = false;
        renderColumnSelects(result.columns);
        await loadDatasets();
    } catch (err) {
        setText(uploadMessage, `上传失败: ${err.message}`);
    }
});

datasetFileInput.addEventListener("change", async () => {
    // 选了新文件后，预览与“当前已上传数据集”可能不一致，先禁止直接作图，避免列名错位。
    pendingFileNeedsUpload = !!datasetFileInput.files?.[0];
    if (pendingFileNeedsUpload) {
        setCurrentDataset(null);
    }
    await detectExcelSheets();
    await previewCurrentFile();
});
sheetNameSelect.addEventListener("change", previewCurrentFile);
refreshDatasetsBtn.addEventListener("click", loadDatasets);
document.getElementById("btn-reset-chart-format").addEventListener("click", () => {
    resetChartFormatToDefaults();
    setText(plotMessage, "已恢复默认图表格式");
});
timeColumnSelect.addEventListener("change", () => {
    resetAxisFormatToDefaults("x");
    setText(plotMessage, "已切换时间列：时间轴格式已恢复默认");
});
addLeftGroupBtn.addEventListener("click", () => addYGroup("left"));
addRightGroupBtn.addEventListener("click", () => addYGroup("right"));

document.getElementById("btn-plot").addEventListener("click", async () => {
    const timeColumn = timeColumnSelect.value;
    const leftYColumns = getYGroupValues(leftYGroupsEl);
    const rightYColumns = getYGroupValues(rightYGroupsEl);
    if (!currentDatasetId) {
        setText(plotMessage, "请先点击“上传数据”生成数据集后再作图");
        return;
    }
    if (pendingFileNeedsUpload) {
        setText(plotMessage, "检测到你已选择新文件，请先上传该文件后再作图");
        return;
    }
    if (!timeColumn || leftYColumns.length === 0 || rightYColumns.length === 0) {
        setText(plotMessage, "请选择时间列与左右轴列（左右轴至少各1列）");
        return;
    }
    if (leftYColumns.includes(timeColumn) || rightYColumns.includes(timeColumn)) {
        setText(plotMessage, "时间列不能与任一Y轴列相同");
        return;
    }
    const duplicates = leftYColumns.filter((col) => rightYColumns.includes(col));
    if (duplicates.length > 0) {
        setText(plotMessage, `左右Y轴列不能重复: ${duplicates.join(", ")}`);
        return;
    }
    let query;
    try {
        query = buildPlotQueryParams(timeColumn, leftYColumns, rightYColumns);
    } catch (e) {
        setText(plotMessage, e.message || String(e));
        return;
    }
    try {
        const result = await requestJson(
            `/analysis/${currentDatasetId}/plot/time-dual-axis?${query.toString()}`,
            { method: "POST" }
        );
        setText(plotMessage, `图表生成成功: ${result.output_path}`);
        plotFrame.src = `/${result.output_path}?t=${Date.now()}`;
    } catch (err) {
        setText(plotMessage, `图表生成失败: ${err.message}`);
        plotFrame.removeAttribute("src");
    }
});

loadDatasets();
renderSeriesColorSettings();
