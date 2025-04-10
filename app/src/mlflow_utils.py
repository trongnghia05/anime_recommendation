import os
import mlflow
import mlflow.pyfunc
from mlflow.tracking import MlflowClient
import pandas as pd
import numpy as np
import tempfile
import logging

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Các cài đặt mặc định
DEFAULT_MLFLOW_TRACKING_URI = os.environ.get('MLFLOW_TRACKING_URI', 'http://localhost:5000')
DEFAULT_EXPERIMENT_NAME = "anime_recommendation_system"
DEFAULT_MODEL_NAME = "anime_recommender"


class AnimeRecommenderWrapper(mlflow.pyfunc.PythonModel):
    """
    Lớp wrapper cho ContentBase để sử dụng với MLflow.
    Cung cấp giao diện chuẩn để MLflow có thể lưu và tải model.
    """

    def __init__(self, recommender):
        self.recommender = recommender

    def predict(self, context, model_input):
        """
        Hàm dự đoán được gọi khi model được phục vụ.
        model_input là DataFrame với cột 'user_id' và tùy chọn 'top_n'

        Args:
            context: MLflow context
            model_input: DataFrame chứa các yêu cầu dự đoán

        Returns:
            list: Danh sách các kết quả đề xuất
        """
        results = []
        for _, row in model_input.iterrows():
            user_id = row['user_id']
            top_n = row.get('top_n', 10)
            try:
                recommendations = self.recommender.recommend(user_id, top_n=top_n)
                results.append(recommendations.to_dict(orient='records'))
            except Exception as e:
                logger.error(f"Lỗi khi tạo đề xuất cho user {user_id}: {e}")
                results.append([])
        return results

    def get_user_profile(self, user_id):
        """
        Lấy profile người dùng

        Args:
            user_id: ID của người dùng

        Returns:
            np.array: Vector profile người dùng
        """
        return self.recommender.get_user_profile(user_id)

    def get_anime_info(self, anime_id):
        """
        Lấy thông tin anime

        Args:
            anime_id: ID của anime

        Returns:
            dict: Thông tin chi tiết của anime
        """
        anime_info = self.recommender.anime_df[self.recommender.anime_df['anime_id'] == anime_id]
        if anime_info.empty:
            return None
        return anime_info.iloc[0].to_dict()


def log_model_to_mlflow(recommender, run_id=None, model_name=DEFAULT_MODEL_NAME):
    """
    Log model vào MLflow

    Args:
        recommender: Đối tượng ContentBase
        run_id: ID của run MLflow (tùy chọn)
        model_name: Tên model để đăng ký

    Returns:
        str: Run ID
    """
    # Thiết lập tracking URI nếu chưa đặt
    if mlflow.get_tracking_uri() is None:
        mlflow.set_tracking_uri(DEFAULT_MLFLOW_TRACKING_URI)

    # Kiểm tra xem đã có run đang hoạt động chưa
    active_run = mlflow.active_run()

    # Nếu đã có run đang hoạt động, sử dụng trực tiếp mà không tạo run mới
    if active_run:
        artifact_uri = active_run.info.artifact_uri
        print(f"Artifacts được lưu tại: {artifact_uri}")
        # Nếu run_id được chỉ định khác với active run, cảnh báo
        if run_id is not None and active_run.info.run_id != run_id:
            logger.warning(f"Run đang hoạt động ({active_run.info.run_id}) khác với run_id được chỉ định ({run_id})")

        # Sử dụng run đang hoạt động
        _log_model_artifacts(recommender, active_run.info.run_id, model_name)
        logger.info(f"Đã log vào run đang hoạt động: {active_run.info.run_id}")
        return active_run.info.run_id

    # Nếu không có run đang hoạt động, tạo mới hoặc mở lại run cũ
    create_new_run = run_id is None
    if create_new_run:
        with mlflow.start_run() as run:
            run_id = run.info.run_id
            _log_model_artifacts(recommender, run_id, model_name)
            logger.info(f"Đã tạo run mới với ID: {run_id}")
    else:
        with mlflow.start_run(run_id=run_id):
            _log_model_artifacts(recommender, run_id, model_name)
            logger.info(f"Đã log vào run có sẵn với ID: {run_id}")

    return run_id


def _log_model_artifacts(recommender, run_id, model_name):
    """
    Hàm nội bộ để log model và artifacts vào MLflow

    Args:
        recommender: Đối tượng ContentBase
        run_id: ID của run MLflow
        model_name: Tên model để đăng ký
    """
    # Log model metrics trước
    mlflow.log_metric("anime_count", len(recommender.anime_df))
    mlflow.log_metric("genre_count", len(recommender.genre_list))
    mlflow.log_metric("user_profiles_count", len(recommender.user_profiles))

    # Log model params
    mlflow.log_param("model_type", "content_based")

    # Wrap model
    wrapped_model = AnimeRecommenderWrapper(recommender)

    # Log model vào MLflow
    mlflow.pyfunc.log_model(
        artifact_path="model",
        python_model=wrapped_model,
        registered_model_name=model_name,
        pip_requirements=["pandas", "numpy", "scipy", "scikit-learn"],
    )

    # Log metadata
    with tempfile.NamedTemporaryFile(suffix='.json', mode='w+') as f:
        pd.Series(recommender.genre_list).to_json(f.name)
        mlflow.log_artifact(f.name, "metadata/genre_list.json")

    logger.info(f"Đã log model và artifacts vào run: {run_id}")


def get_latest_model_info(model_name=DEFAULT_MODEL_NAME):
    """
    Lấy thông tin phiên bản model mới nhất

    Args:
        model_name: Tên model

    Returns:
        dict: Thông tin model
    """
    client = MlflowClient()

    # Tìm phiên bản mới nhất dựa trên version number
    versions = []
    for model_version in client.search_model_versions(f"name='{model_name}'"):
        versions.append((int(model_version.version), model_version))

    if versions:
        # Sắp xếp theo phiên bản giảm dần và lấy phiên bản cao nhất
        versions.sort(reverse=True)
        latest_model = versions[0][1]

        return {
            "name": latest_model.name,
            "version": latest_model.version,
            "stage": latest_model.current_stage,
            "run_id": latest_model.run_id
        }

    return None


def load_model_from_registry(model_name=DEFAULT_MODEL_NAME):
    """
    Tải model mới nhất từ MLflow Model Registry

    Args:
        model_name: Tên model

    Returns:
        object: Model PyFunc
    """
    try:
        # Lấy thông tin model mới nhất
        model_info = get_latest_model_info(model_name)

        if not model_info:
            logger.error(f"Không tìm thấy model {model_name} trong registry")
            return None

        # Tải model dựa trên phiên bản
        model_uri = f"models:/{model_name}/{model_info['version']}"
        model = mlflow.pyfunc.load_model(model_uri)
        logger.info(f"Đã tải model {model_name} phiên bản {model_info['version']}")
        return model

    except Exception as e:
        logger.error(f"Lỗi khi tải model: {e}")
        raise


# def setup_mlflow(tracking_uri=None, experiment_name=DEFAULT_EXPERIMENT_NAME):
#     """
#     Thiết lập MLflow tracking server và experiment
#     """
#     # Thiết lập tracking URI
#     if tracking_uri is None:
#         tracking_uri = DEFAULT_MLFLOW_TRACKING_URI
#
#     mlflow.set_tracking_uri(tracking_uri)
#     logger.info(f"Đã thiết lập MLflow tracking URI: {tracking_uri}")
#
#     # Xác định artifact_location là đường dẫn cục bộ
#     artifact_location = "file:///mlflow-artifacts"
#
#     # Tìm hoặc tạo experiment
#     try:
#         experiment = mlflow.get_experiment_by_name(experiment_name)
#         if experiment:
#             experiment_id = experiment.experiment_id
#             logger.info(f"Đã tìm thấy experiment '{experiment_name}' với ID: {experiment_id}")
#         else:
#             # Tạo experiment với artifact_location cục bộ
#             experiment_id = mlflow.create_experiment(
#                 experiment_name,
#                 artifact_location=artifact_location
#             )
#             logger.info(f"Đã tạo experiment mới '{experiment_name}' với ID: {experiment_id}")
#
#         mlflow.set_experiment(experiment_name)
#         return experiment_id
#
#     except Exception as e:
#         logger.error(f"Lỗi khi thiết lập MLflow experiment: {e}")
#         raise

def setup_mlflow(tracking_uri=None, experiment_name=DEFAULT_EXPERIMENT_NAME):
    """
    Thiết lập MLflow tracking server và experiment
    """
    # Thiết lập tracking URI
    if tracking_uri is None:
        tracking_uri = DEFAULT_MLFLOW_TRACKING_URI
    print("tracking_uri: ", tracking_uri)
    mlflow.set_tracking_uri(tracking_uri)
    logger.info(f"Đã thiết lập MLflow tracking URI: {tracking_uri}")

    # Thiết lập thông tin xác thực S3/MinIO
    os.environ['AWS_ACCESS_KEY_ID'] = 'minioadmin'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'minioadmin'
    os.environ['MLFLOW_S3_ENDPOINT_URL'] = 'http://minio:9000'

    # Tìm hoặc tạo experiment
    try:
        experiment = mlflow.get_experiment_by_name(experiment_name)
        if experiment:
            experiment_id = experiment.experiment_id
            logger.info(f"Đã tìm thấy experiment '{experiment_name}' với ID: {experiment_id}")
        else:
            # Tạo experiment với artifact_location trong S3
            experiment_id = mlflow.create_experiment(
                experiment_name,
                artifact_location="s3://mlflow"
            )
            logger.info(f"Đã tạo experiment mới '{experiment_name}' với ID: {experiment_id}")

        mlflow.set_experiment(experiment_name)
        return experiment_id

    except Exception as e:
        logger.error(f"Lỗi khi thiết lập MLflow experiment: {e}")
        raise

def evaluate_and_log_metrics(recommender, metrics, run_id=None):
    """
    Log metrics đánh giá vào MLflow

    Args:
        recommender: Đối tượng ContentBase
        metrics: Dict chứa metrics đánh giá
        run_id: ID của run MLflow (tùy chọn)

    Returns:
        str: Run ID
    """
    # Thiết lập tracking URI nếu chưa đặt
    if mlflow.get_tracking_uri() is None:
        mlflow.set_tracking_uri(DEFAULT_MLFLOW_TRACKING_URI)

    # Kiểm tra xem đã có run đang hoạt động chưa
    active_run = mlflow.active_run()

    # Nếu đã có run đang hoạt động, sử dụng trực tiếp mà không tạo run mới
    if active_run:
        # Nếu run_id được chỉ định khác với active run, cảnh báo
        if run_id is not None and active_run.info.run_id != run_id:
            logger.warning(f"Run đang hoạt động ({active_run.info.run_id}) khác với run_id được chỉ định ({run_id})")

        # Sử dụng run đang hoạt động
        _log_evaluation_metrics(metrics)
        logger.info(f"Đã log metrics vào run đang hoạt động: {active_run.info.run_id}")
        return active_run.info.run_id

    # Nếu không có run đang hoạt động, tạo mới hoặc mở lại run cũ
    create_new_run = run_id is None
    if create_new_run:
        with mlflow.start_run() as run:
            run_id = run.info.run_id
            _log_evaluation_metrics(metrics)
            logger.info(f"Đã tạo run mới với ID: {run_id}")
    else:
        with mlflow.start_run(run_id=run_id):
            _log_evaluation_metrics(metrics)
            logger.info(f"Đã log vào run có sẵn với ID: {run_id}")

    return run_id


def _log_evaluation_metrics(metrics):
    """
    Hàm nội bộ để log metrics đánh giá

    Args:
        metrics: Dict chứa metrics đánh giá
    """
    # Log metrics cơ bản
    mlflow.log_metric("user_count", metrics['user_count'])
    mlflow.log_metric("hit_rate", metrics['hit_rate'])
    mlflow.log_metric("mean_reciprocal_rank", metrics['mean_reciprocal_rank'])
    mlflow.log_metric("catalog_coverage", metrics['catalog_coverage'])
    mlflow.log_metric("prediction_coverage", metrics['prediction_coverage'])

    # Log metrics theo k
    for k in metrics['precision']:
        mlflow.log_metric(f"precision_at_{k}", metrics['precision'][k])
        mlflow.log_metric(f"recall_at_{k}", metrics['recall'][k])
        mlflow.log_metric(f"ndcg_at_{k}", metrics['ndcg'][k])

    logger.info("Đã log evaluation metrics vào MLflow")