from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import BasicStatsResponse, PlotResponse
from app.services.analysis_service import compute_basic_stats, load_dataframe
from app.services.data_service import get_dataset_or_404
from app.services.plot_service import generate_dual_axis_line_plot

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/{dataset_id}/stats", response_model=BasicStatsResponse)
def get_basic_stats(dataset_id: int, db: Session = Depends(get_db)):
    dataset = get_dataset_or_404(db, dataset_id)
    df = load_dataframe(dataset)
    numeric_columns, describe = compute_basic_stats(df)
    return BasicStatsResponse(
        dataset_id=dataset.id, numeric_columns=numeric_columns, describe=describe
    )


@router.post("/{dataset_id}/plot/time-dual-axis", response_model=PlotResponse)
def create_time_dual_axis_plot(
    dataset_id: int,
    time_column: str = Query(..., description="时间列名"),
    left_y_columns: list[str] = Query(..., description="左侧 Y 轴列名（可多选）"),
    right_y_columns: list[str] = Query(..., description="右侧 Y 轴列名（可多选）"),
    x_min: str | None = Query(default=None, description="时间轴下限（与数据时间格式一致，需与 x_max 同时填）"),
    x_max: str | None = Query(default=None, description="时间轴上限"),
    y_left_min: float | None = Query(default=None, description="左 Y 轴下限"),
    y_left_max: float | None = Query(default=None, description="左 Y 轴上限"),
    y_right_min: float | None = Query(default=None, description="右 Y 轴下限"),
    y_right_max: float | None = Query(default=None, description="右 Y 轴上限"),
    x_dtick_hours: float | None = Query(
        default=None,
        description="时间轴主刻度间隔（小时），将转为 Plotly 毫秒 dtick；留空为自动",
    ),
    y_left_dtick: float | None = Query(default=None, description="左 Y 轴刻度间隔，留空为自动"),
    y_right_dtick: float | None = Query(default=None, description="右 Y 轴刻度间隔，留空为自动"),
    chart_title: str | None = Query(default=None, description="图表标题（可选）"),
    x_title: str | None = Query(default=None, description="X 轴标题（可选）"),
    y_left_title: str | None = Query(default=None, description="左 Y 轴标题（可选）"),
    y_right_title: str | None = Query(default=None, description="右 Y 轴标题（可选）"),
    series_colors_json: str | None = Query(
        default=None,
        description='按列名配置颜色的 JSON，例如 {"温度1(℃)":"#ff0000"}',
    ),
    db: Session = Depends(get_db),
):
    dataset = get_dataset_or_404(db, dataset_id)
    df = load_dataframe(dataset)
    output_path = generate_dual_axis_line_plot(
        df,
        dataset_id,
        time_column=time_column,
        left_y_columns=left_y_columns,
        right_y_columns=right_y_columns,
        x_min=x_min,
        x_max=x_max,
        y_left_min=y_left_min,
        y_left_max=y_left_max,
        y_right_min=y_right_min,
        y_right_max=y_right_max,
        x_dtick_hours=x_dtick_hours,
        y_left_dtick=y_left_dtick,
        y_right_dtick=y_right_dtick,
        chart_title=chart_title,
        x_title=x_title,
        y_left_title=y_left_title,
        y_right_title=y_right_title,
        series_colors_json=series_colors_json,
    )
    return PlotResponse(
        dataset_id=dataset.id, plot_type="time_dual_axis_line", output_path=output_path
    )
