import re
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import HTTPException
import plotly.graph_objects as go
from plotly.subplots import make_subplots

PLOT_DIR = Path("plots")

_HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")


def _validate_hex_color(value: str) -> str:
    v = value.strip()
    if _HEX_COLOR.match(v):
        return v
    raise HTTPException(
        status_code=400,
        detail=f"颜色须为 #RRGGBB 十六进制格式，当前: {value}",
    )


DEFAULT_SERIES_COLORS = [
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
]


def _parse_series_color_map(series_colors_json: str | None) -> dict[str, str]:
    if series_colors_json is None or series_colors_json.strip() == "":
        return {}
    try:
        raw = json.loads(series_colors_json)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"series_colors_json 不是合法 JSON: {exc}") from exc
    if not isinstance(raw, dict):
        raise HTTPException(status_code=400, detail="series_colors_json 必须是对象，键为列名，值为颜色")
    result: dict[str, str] = {}
    for k, v in raw.items():
        key = str(k).strip()
        if not key:
            continue
        result[key] = _validate_hex_color(str(v))
    return result


def generate_dual_axis_line_plot(
    df: pd.DataFrame,
    dataset_id: int,
    time_column: str,
    left_y_columns: list[str],
    right_y_columns: list[str],
    *,
    x_min: str | None = None,
    x_max: str | None = None,
    y_left_min: float | None = None,
    y_left_max: float | None = None,
    y_right_min: float | None = None,
    y_right_max: float | None = None,
    x_dtick_hours: float | None = None,
    y_left_dtick: float | None = None,
    y_right_dtick: float | None = None,
    chart_title: str | None = None,
    x_title: str | None = None,
    y_left_title: str | None = None,
    y_right_title: str | None = None,
    series_colors_json: str | None = None,
) -> str:
    selected_columns = [time_column, *left_y_columns, *right_y_columns]
    for col in selected_columns:
        if col not in df.columns:
            raise HTTPException(status_code=400, detail=f"列不存在: {col}")
    if not left_y_columns:
        raise HTTPException(status_code=400, detail="请至少选择一列左 Y 轴数据")
    if not right_y_columns:
        raise HTTPException(status_code=400, detail="请至少选择一列右 Y 轴数据")
    if time_column in set(left_y_columns) or time_column in set(right_y_columns):
        raise HTTPException(status_code=400, detail="时间列不能与任一 Y 轴列相同")
    duplicated_y_columns = set(left_y_columns).intersection(set(right_y_columns))
    if duplicated_y_columns:
        dup = ", ".join(sorted(duplicated_y_columns))
        raise HTTPException(status_code=400, detail=f"左右 Y 轴列不能重复: {dup}")
    for col in left_y_columns:
        if not pd.api.types.is_numeric_dtype(df[col]):
            raise HTTPException(status_code=400, detail=f"左 Y 轴列不是数值类型: {col}")
    for col in right_y_columns:
        if not pd.api.types.is_numeric_dtype(df[col]):
            raise HTTPException(status_code=400, detail=f"右 Y 轴列不是数值类型: {col}")

    series_color_map = _parse_series_color_map(series_colors_json)

    if (y_left_min is not None) ^ (y_left_max is not None):
        raise HTTPException(status_code=400, detail="左 Y 轴需同时填写下限与上限，或均留空")
    if y_left_min is not None and y_left_max is not None and y_left_min >= y_left_max:
        raise HTTPException(status_code=400, detail="左 Y 轴下限须小于上限")
    if (y_right_min is not None) ^ (y_right_max is not None):
        raise HTTPException(status_code=400, detail="右 Y 轴需同时填写下限与上限，或均留空")
    if y_right_min is not None and y_right_max is not None and y_right_min >= y_right_max:
        raise HTTPException(status_code=400, detail="右 Y 轴下限须小于上限")
    if (x_min and not x_max) or (x_max and not x_min):
        raise HTTPException(status_code=400, detail="时间轴需同时填写起止，或均留空")

    PLOT_DIR.mkdir(parents=True, exist_ok=True)
    left_name = "_".join(left_y_columns[:2])
    right_name = "_".join(right_y_columns[:2])
    output_name = (
        f"dataset_{dataset_id}_{left_name}_{right_name}_line_"
        f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.html"
    )
    output_path = PLOT_DIR / output_name

    try:
        plot_df = df[[time_column, *left_y_columns, *right_y_columns]].copy()
        plot_df[time_column] = pd.to_datetime(plot_df[time_column], errors="coerce")
        plot_df = plot_df.dropna(subset=[time_column]).sort_values(by=time_column)
        if plot_df.empty:
            raise HTTPException(status_code=400, detail="可用于绘图的数据为空，请检查列内容")

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        series_index = 0
        for col in left_y_columns:
            axis_df = plot_df.dropna(subset=[col])
            if axis_df.empty:
                continue
            color = series_color_map.get(col, DEFAULT_SERIES_COLORS[series_index % len(DEFAULT_SERIES_COLORS)])
            series_index += 1
            fig.add_trace(
                go.Scatter(
                    x=axis_df[time_column],
                    y=axis_df[col],
                    mode="lines+markers",
                    name=col,
                    line={"color": color},
                    marker={"color": color},
                ),
                secondary_y=False,
            )
        for col in right_y_columns:
            axis_df = plot_df.dropna(subset=[col])
            if axis_df.empty:
                continue
            color = series_color_map.get(col, DEFAULT_SERIES_COLORS[series_index % len(DEFAULT_SERIES_COLORS)])
            series_index += 1
            fig.add_trace(
                go.Scatter(
                    x=axis_df[time_column],
                    y=axis_df[col],
                    mode="lines+markers",
                    name=col,
                    line={"color": color},
                    marker={"color": color},
                ),
                secondary_y=True,
            )
        if not fig.data:
            raise HTTPException(status_code=400, detail="所选列均无有效数值，无法绘图")

        resolved_title = (chart_title or "").strip() or f"左轴({', '.join(left_y_columns)}) / 右轴({', '.join(right_y_columns)})"
        resolved_x_title = (x_title or "").strip() or time_column
        resolved_y_left_title = (y_left_title or "").strip() or "左 Y 轴"
        resolved_y_right_title = (y_right_title or "").strip() or "右 Y 轴"

        fig.update_layout(
            title=resolved_title,
            title_x=0.5,
            title_font={"size": 20},
            hovermode="x unified",
            xaxis_title=resolved_x_title,
            legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0},
            margin={"l": 60, "r": 60, "t": 60, "b": 50},
        )
        fig.update_yaxes(title_text=resolved_y_left_title, secondary_y=False)
        fig.update_yaxes(title_text=resolved_y_right_title, secondary_y=True)

        xaxis_patch: dict[str, Any] = {"rangeslider": {"visible": True}}
        if x_min and x_max:
            try:
                rx0 = pd.to_datetime(x_min)
                rx1 = pd.to_datetime(x_max)
            except Exception as exc:
                raise HTTPException(status_code=400, detail=f"时间轴范围解析失败: {exc}") from exc
            if pd.isna(rx0) or pd.isna(rx1):
                raise HTTPException(status_code=400, detail="时间轴起止无法解析为有效时间")
            xaxis_patch["range"] = [rx0.isoformat(), rx1.isoformat()]
        if x_dtick_hours is not None:
            if x_dtick_hours <= 0:
                raise HTTPException(status_code=400, detail="时间轴间隔（小时）须为正数")
            xaxis_patch["dtick"] = x_dtick_hours * 3600 * 1000
        fig.update_xaxes(**xaxis_patch)

        y_left_patch: dict[str, Any] = {}
        if y_left_min is not None and y_left_max is not None:
            y_left_patch["range"] = [y_left_min, y_left_max]
        if y_left_dtick is not None:
            if y_left_dtick <= 0:
                raise HTTPException(status_code=400, detail="左 Y 轴刻度间隔须为正数")
            y_left_patch["dtick"] = y_left_dtick
        if y_left_patch:
            fig.update_yaxes(**y_left_patch, secondary_y=False)

        y_right_patch: dict[str, Any] = {}
        if y_right_min is not None and y_right_max is not None:
            y_right_patch["range"] = [y_right_min, y_right_max]
        if y_right_dtick is not None:
            if y_right_dtick <= 0:
                raise HTTPException(status_code=400, detail="右 Y 轴刻度间隔须为正数")
            y_right_patch["dtick"] = y_right_dtick
        if y_right_patch:
            fig.update_yaxes(**y_right_patch, secondary_y=True)

        # 分发版要求完全离线可用，因此 Plotly JS 直接内嵌到 HTML
        fig.write_html(str(output_path), include_plotlyjs=True, full_html=True)
        return str(output_path)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"时间列解析失败: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"绘图失败: {exc}") from exc
