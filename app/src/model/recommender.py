import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix, lil_matrix
import pickle
import time
import os
from collections import defaultdict
from sklearn.model_selection import train_test_split


class ContentBase:
    """
    ContentBase Recommender System dựa trên thể loại anime.
    Sử dụng mô hình content-based filtering để đề xuất anime cho người dùng
    dựa trên sở thích thể loại.
    """

    def __init__(self, cache_dir="./cache"):
        # Thông tin cơ bản
        self.anime_df = None
        self.genre_list = None
        self.anime_id_map = None
        self.reverse_anime_id_map = None

        # Ma trận và ánh xạ
        self.anime_genre_matrix = None
        self.genre_to_idx = None

        # Cache cho user profiles
        self.user_profiles = {}
        self.cache_dir = cache_dir

        # Đảm bảo thư mục cache tồn tại
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

    def preprocess_data(self, anime_path):
        """
        Tiền xử lý dữ liệu anime và xây dựng Anime-Genre Matrix.
        Chỉ cần thực hiện một lần duy nhất.

        Args:
            anime_path: Đường dẫn đến file anime.csv

        Returns:
            bool: True nếu xử lý thành công
        """
        print("Bắt đầu tiền xử lý dữ liệu anime...")
        start_time = time.time()

        # 1. Đọc dữ liệu anime, chỉ đọc các cột cần thiết
        try:
            # Xác định các cột cần thiết
            columns_to_use = None  # Đọc tất cả cột đầu tiên để xác định cấu trúc
            anime_df = pd.read_csv(anime_path)

            # Xác định các cột cần thiết
            id_col = next((col for col in anime_df.columns if 'id' in col.lower()), anime_df.columns[0])
            name_col = next((col for col in anime_df.columns if 'name' in col.lower()), None)
            genre_col = next((col for col in anime_df.columns if 'genre' in col.lower()), None)
            score_col = next((col for col in anime_df.columns if 'score' in col.lower()), None)

            # Chuẩn bị danh sách cột cần thiết
            necessary_cols = [id_col]
            if name_col: necessary_cols.append(name_col)
            if genre_col: necessary_cols.append(genre_col)
            if score_col: necessary_cols.append(score_col)

            # Đọc lại chỉ với các cột cần thiết
            if len(necessary_cols) < len(anime_df.columns):
                anime_df = pd.read_csv(anime_path, usecols=necessary_cols)
                print(f"Chỉ đọc {len(necessary_cols)} cột cần thiết thay vì {len(anime_df.columns)} cột")

            # Chuẩn hóa tên cột
            col_mapping = {
                id_col: 'anime_id',
                name_col: 'name' if name_col else None,
                genre_col: 'genres' if genre_col else None,
                score_col: 'score' if score_col else None
            }
            col_mapping = {k: v for k, v in col_mapping.items() if k is not None and v is not None}
            anime_df.rename(columns=col_mapping, inplace=True)

            # Đảm bảo các cột cần thiết tồn tại
            if 'genres' not in anime_df.columns:
                anime_df['genres'] = ''
                print("Warning: Không tìm thấy cột thể loại, tạo cột trống 'genres'")

        except Exception as e:
            print(f"Lỗi khi đọc dữ liệu anime: {e}")
            raise

        # 2. Tạo mapping cho anime_id để tối ưu bộ nhớ
        unique_anime_ids = anime_df['anime_id'].unique()
        self.anime_id_map = {original_id: idx for idx, original_id in enumerate(unique_anime_ids)}
        self.reverse_anime_id_map = {idx: original_id for idx, original_id in enumerate(unique_anime_ids)}

        # 3. Trích xuất tất cả các thể loại
        all_genres = set()
        for genres in anime_df['genres'].dropna():
            for genre in str(genres).split(','):
                genre = genre.strip()
                if genre:  # Đảm bảo không thêm genre rỗng
                    all_genres.add(genre)

        self.genre_list = sorted(list(all_genres))
        self.genre_to_idx = {genre: i for i, genre in enumerate(self.genre_list)}

        print(f"Tìm thấy {len(self.genre_list)} thể loại anime từ {len(unique_anime_ids)} anime")

        # 4. Xây dựng ma trận Anime-Genre (ma trận thưa)
        print("Bắt đầu xây dựng Anime-Genre Matrix...")
        anime_genre_matrix = lil_matrix((len(unique_anime_ids), len(self.genre_list)), dtype=np.float32)

        for idx, row in anime_df.iterrows():
            anime_idx = self.anime_id_map[row['anime_id']]
            if pd.notna(row['genres']):
                for genre in str(row['genres']).split(','):
                    genre = genre.strip()
                    if genre in self.genre_to_idx:
                        anime_genre_matrix[anime_idx, self.genre_to_idx[genre]] = 1.0

        # Chuyển đổi sang CSR format để tối ưu phép nhân
        self.anime_genre_matrix = anime_genre_matrix.tocsr()

        # 5. Lưu DataFrame đã xử lý
        self.anime_df = anime_df

        print(f"Tiền xử lý dữ liệu hoàn tất trong {time.time() - start_time:.2f} giây")

        # Lưu các dữ liệu đã xử lý
        self.save_preprocessed_data()

        return True

    def save_preprocessed_data(self):
        """Lưu dữ liệu đã tiền xử lý vào cache"""
        data = {
            'anime_df': self.anime_df,
            'genre_list': self.genre_list,
            'genre_to_idx': self.genre_to_idx,
            'anime_id_map': self.anime_id_map,
            'reverse_anime_id_map': self.reverse_anime_id_map,
            'anime_genre_matrix': self.anime_genre_matrix
        }
        with open(os.path.join(self.cache_dir, 'anime_preprocessed.pkl'), 'wb') as f:
            pickle.dump(data, f)
        print(f"Dữ liệu tiền xử lý đã được lưu vào {self.cache_dir}")

    def load_preprocessed_data(self):
        """
        Tải dữ liệu đã tiền xử lý từ cache

        Returns:
            bool: True nếu tải thành công, False nếu thất bại
        """
        try:
            with open(os.path.join(self.cache_dir, 'anime_preprocessed.pkl'), 'rb') as f:
                data = pickle.load(f)

            self.anime_df = data['anime_df']
            self.genre_list = data['genre_list']
            self.genre_to_idx = data['genre_to_idx']
            self.anime_id_map = data['anime_id_map']
            self.reverse_anime_id_map = data['reverse_anime_id_map']
            self.anime_genre_matrix = data['anime_genre_matrix']

            print(f"Dữ liệu tiền xử lý đã được tải từ cache")
            return True
        except Exception as e:
            print(f"Lỗi khi tải dữ liệu tiền xử lý: {e}")
            return False

    def process_user_data(self, animelist_df, force_rebuild=False):
        """
        Xử lý dữ liệu đánh giá của người dùng.

        Args:
            animelist_df: DataFrame chứa dữ liệu đánh giá anime của người dùng
            force_rebuild: Xây dựng lại user profiles ngay cả khi đã có trong cache

        Returns:
            bool: True nếu xử lý thành công
        """
        print("Xử lý dữ liệu người dùng...")

        # Chuẩn hóa tên cột
        animelist_df.columns = [col.lower() for col in animelist_df.columns]

        # Xác định các cột cần thiết
        user_id_col = next((col for col in animelist_df.columns if 'user' in col.lower()), animelist_df.columns[0])
        anime_id_col = next((col for col in animelist_df.columns if 'anime' in col.lower()), animelist_df.columns[1])
        rating_col = next((col for col in animelist_df.columns if 'rat' in col.lower() or 'score' in col.lower()), None)

        # Đổi tên cột
        col_mapping = {
            user_id_col: 'user_id',
            anime_id_col: 'anime_id'
        }
        if rating_col:
            col_mapping[rating_col] = 'rating'

        animelist_df.rename(columns=col_mapping, inplace=True)

        # Đảm bảo có cột rating
        if 'rating' not in animelist_df.columns:
            animelist_df['rating'] = 5.0  # Giá trị mặc định
            print("Warning: Không tìm thấy cột đánh giá, sử dụng giá trị mặc định 5.0")

        # Lưu DataFrame
        self.animelist_df = animelist_df

        # Xóa tất cả cache user profile nếu cần
        if force_rebuild:
            self.user_profiles = {}
            cache_files = [f for f in os.listdir(self.cache_dir) if f.startswith('user_profile_')]
            for file in cache_files:
                os.remove(os.path.join(self.cache_dir, file))
            print("Đã xóa cache của tất cả user profiles")

        return True

    def get_user_profile(self, user_id, force_recalculate=False):
        """
        Lấy profile thể loại cho người dùng.
        Sử dụng cache nếu có, nếu không thì tính toán mới.

        Args:
            user_id: ID của người dùng
            force_recalculate: Tính toán lại ngay cả khi đã có trong cache

        Returns:
            np.array: Vector profile người dùng
        """
        cache_file = os.path.join(self.cache_dir, f'user_profile_{user_id}.pkl')

        # Kiểm tra cache trong memory
        if not force_recalculate and user_id in self.user_profiles:
            return self.user_profiles[user_id]

        # Kiểm tra cache trong file
        if not force_recalculate and os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    user_profile = pickle.load(f)
                self.user_profiles[user_id] = user_profile
                return user_profile
            except Exception:
                pass  # Nếu đọc cache lỗi, tính toán lại

        # Tính toán mới
        return self.calculate_user_profile(user_id)

    def calculate_user_profile(self, user_id, override_ratings=None):
        """
        Tính toán profile thể loại cho người dùng.
        Có thể ghi đè bằng cách cung cấp override_ratings DataFrame.

        Args:
            user_id: ID của người dùng
            override_ratings: DataFrame chứa đánh giá thay thế (tùy chọn)

        Returns:
            np.array: Vector profile người dùng
        """
        # Nếu không có override_ratings và đã có trong cache, trả về từ cache
        if override_ratings is None and user_id in self.user_profiles:
            return self.user_profiles[user_id]

        # Nếu không có override_ratings và có cache trong file
        cache_file = os.path.join(self.cache_dir, f'user_profile_{user_id}.pkl')
        if override_ratings is None and os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    user_profile = pickle.load(f)
                self.user_profiles[user_id] = user_profile
                return user_profile
            except Exception:
                pass  # Nếu đọc cache lỗi, tính toán lại

        # Xác định ratings để sử dụng
        start_time = time.time()

        if override_ratings is not None:
            user_ratings = override_ratings
        else:
            # Lấy danh sách anime người dùng đã đánh giá
            user_ratings = self.animelist_df[self.animelist_df['user_id'] == user_id]

        if len(user_ratings) == 0:
            print(f"User {user_id} không có đánh giá nào")
            return np.zeros(len(self.genre_list), dtype=np.float32)

        # Sử dụng defaultdict để tối ưu
        genre_weights = defaultdict(float)
        genre_counts = defaultdict(int)

        # Duyệt qua từng anime đã đánh giá
        processed_count = 0
        for _, rating in user_ratings.iterrows():
            anime_id = rating['anime_id']
            if anime_id in self.anime_id_map:
                anime_idx = self.anime_id_map[anime_id]

                # Lấy đánh giá của người dùng
                user_score = rating['rating']
                if pd.isna(user_score):
                    user_score = 5.0

                # Lấy thể loại của anime từ ma trận
                genre_indices = self.anime_genre_matrix[anime_idx].nonzero()[1]

                # Cập nhật trọng số cho từng thể loại
                for genre_idx in genre_indices:
                    genre = self.genre_list[genre_idx]
                    genre_weights[genre] += user_score
                    genre_counts[genre] += 1

                processed_count += 1

        # Tạo vector profile người dùng
        user_profile = np.zeros(len(self.genre_list), dtype=np.float32)

        # Điền giá trị vào vector
        for genre, count in genre_counts.items():
            if count > 0 and genre in self.genre_to_idx:
                idx = self.genre_to_idx[genre]
                user_profile[idx] = genre_weights[genre] / count

        # Cache kết quả
        if override_ratings is None:
            self.user_profiles[user_id] = user_profile

            # Lưu vào file
            with open(cache_file, 'wb') as f:
                pickle.dump(user_profile, f)

            print(f"Đã tính profile người dùng từ {processed_count} anime trong {time.time() - start_time:.2f} giây")

        return user_profile

    def recommend(self, user_id, top_n=10, user_profile=None, exclude_seen=True):
        """
        Đề xuất anime cho người dùng.
        Sử dụng ma trận đã tính trước và profile người dùng.

        Args:
            user_id: ID của người dùng
            top_n: Số lượng đề xuất tối đa
            user_profile: Vector profile người dùng đã tính sẵn (tùy chọn)
            exclude_seen: Có loại bỏ anime đã xem không

        Returns:
            DataFrame: Kết quả đề xuất
        """
        start_time = time.time()

        # 1. Lấy profile người dùng (hoặc sử dụng profile đã tính sẵn)
        if user_profile is None:
            user_profile = self.get_user_profile(user_id)

        # In ra top thể loại yêu thích
        top_genres_idx = np.argsort(-user_profile)[:5]
        print("\nTop 5 thể loại yêu thích của người dùng:")
        for idx in top_genres_idx:
            if user_profile[idx] > 0:
                print(f"- {self.genre_list[idx]}: {user_profile[idx]:.2f}")

        # 2. Tính điểm dự đoán bằng phép nhân ma trận
        predicted_scores = self.anime_genre_matrix.dot(user_profile)

        # 3. Lấy danh sách anime đã xem nếu cần
        if exclude_seen:
            user_ratings = self.animelist_df[self.animelist_df['user_id'] == user_id]
            seen_anime_ids = set(user_ratings['anime_id'])

            # Xây dựng mask cho anime chưa xem
            mask = np.ones(len(predicted_scores), dtype=bool)
            for anime_id in seen_anime_ids:
                if anime_id in self.anime_id_map:
                    mask[self.anime_id_map[anime_id]] = False

            # 4. Áp dụng mask để loại bỏ anime đã xem
            filtered_scores = predicted_scores[mask]
            filtered_indices = np.arange(len(predicted_scores))[mask]
        else:
            # Nếu không loại bỏ đã xem, sử dụng tất cả
            filtered_scores = predicted_scores
            filtered_indices = np.arange(len(predicted_scores))

        # 5. Sắp xếp và lấy top-N (sử dụng partial sort để tối ưu)
        if len(filtered_scores) > top_n * 2:
            # Chỉ tìm top_n*2 indices lớn nhất (không sắp xếp toàn bộ)
            top_n_times_2_indices = np.argpartition(-filtered_scores, min(top_n * 2, len(filtered_scores) - 1))[
                                    :top_n * 2]
            # Sắp xếp chỉ top_n*2 phần tử đó
            top_n_indices = top_n_times_2_indices[np.argsort(-filtered_scores[top_n_times_2_indices])][:top_n]
        else:
            # Nếu ít phần tử, sắp xếp toàn bộ
            top_n_indices = np.argsort(-filtered_scores)[:min(top_n, len(filtered_scores))]

        # 6. Ánh xạ ngược về anime_id gốc
        recommended_anime_indices = filtered_indices[top_n_indices]
        recommended_anime_ids = [self.reverse_anime_id_map[idx] for idx in recommended_anime_indices]

        # 7. Tạo DataFrame kết quả với thông tin chi tiết
        results = []
        for i, anime_id in enumerate(recommended_anime_ids):
            anime_idx = self.anime_id_map[anime_id]
            anime_info = self.anime_df[self.anime_df['anime_id'] == anime_id]

            if not anime_info.empty:
                # Lấy thông tin cần thiết
                anime_name = anime_info['name'].values[0] if 'name' in anime_info.columns and pd.notna(
                    anime_info['name'].values[0]) else f"Anime {anime_id}"
                anime_genres = anime_info['genres'].values[0] if 'genres' in anime_info.columns and pd.notna(
                    anime_info['genres'].values[0]) else "Unknown"
                anime_score = anime_info['score'].values[0] if 'score' in anime_info.columns and pd.notna(
                    anime_info['score'].values[0]) else "N/A"

                # Tạo giải thích
                prediction_score = predicted_scores[anime_idx]

                # Tìm thể loại khớp với sở thích người dùng
                genre_list = [g.strip() for g in str(anime_genres).split(',')]
                matching_genres = []

                for genre in genre_list:
                    if genre in self.genre_to_idx:
                        genre_idx = self.genre_to_idx[genre]
                        user_genre_score = user_profile[genre_idx]
                        if user_genre_score > 0:
                            matching_genres.append((genre, user_genre_score))

                # Sắp xếp theo điểm số
                matching_genres.sort(key=lambda x: x[1], reverse=True)

                # Tạo giải thích
                if matching_genres:
                    explanation = f"Thể loại phù hợp: {', '.join([g[0] for g in matching_genres[:3]])}"
                else:
                    explanation = "Đề xuất dựa trên các yếu tố khác"

                # Thêm vào kết quả
                results.append({
                    'rank': i + 1,
                    'anime_id': anime_id,
                    'name': anime_name,
                    'genres': anime_genres,
                    'score': anime_score,
                    'prediction': prediction_score,
                    'explanation': explanation
                })

        recommendations_df = pd.DataFrame(results)
        print(f"Đã tạo {len(results)} đề xuất trong {time.time() - start_time:.2f} giây")

        return recommendations_df

    def evaluate(self, test_size=0.2, k_values=[5, 10], random_state=42, max_users=100):
        """
        Đánh giá model recommender sử dụng phương pháp hold-out evaluation.

        Args:
            test_size: Tỷ lệ dữ liệu giữ lại cho test, mặc định là 0.2 (20%)
            k_values: Danh sách các giá trị k để tính Precision@k, Recall@k, NDCG@k
            random_state: Seed cho việc chia ngẫu nhiên dữ liệu
            max_users: Số lượng người dùng tối đa để đánh giá

        Returns:
            dict: Từ điển chứa các metrics đánh giá
        """
        print(f"Bắt đầu đánh giá model recommender...")

        # Metrics tổng hợp
        metrics = {
            'user_count': 0,
            'precision': {k: [] for k in k_values},
            'recall': {k: [] for k in k_values},
            'ndcg': {k: [] for k in k_values},
            'hit_rate': [],
            'mean_reciprocal_rank': [],
            'catalog_coverage': 0,
            'prediction_coverage': 0
        }

        # Lấy tất cả user_id duy nhất
        user_ids = self.animelist_df['user_id'].unique()

        # Giới hạn số lượng người dùng để đánh giá
        np.random.seed(random_state)
        eval_users = np.random.choice(user_ids, size=min(max_users, len(user_ids)), replace=False)

        # Set để lưu tất cả anime_id đã đề xuất
        all_anime_ids = set(self.anime_df['anime_id'])
        recommended_anime_ids = set()

        # Đếm số người dùng có ít nhất một đề xuất
        users_with_recommendations = 0

        start_time = time.time()
        print(f"Đánh giá với {len(eval_users)} người dùng...")

        # Với mỗi người dùng
        for idx, user_id in enumerate(eval_users):
            # Hiển thị tiến độ
            if (idx + 1) % 10 == 0:
                elapsed = time.time() - start_time
                print(f"Đã xử lý {idx + 1}/{len(eval_users)} người dùng ({elapsed:.2f}s)")

            # Lấy dữ liệu đánh giá của người dùng
            user_ratings = self.animelist_df[self.animelist_df['user_id'] == user_id]

            # Bỏ qua người dùng có ít hơn 5 đánh giá (không thể chia train/test đáng tin cậy)
            if len(user_ratings) < 5:
                continue

            # Chia thành train và test
            train_ratings, test_ratings = train_test_split(
                user_ratings, test_size=test_size, random_state=random_state
            )

            # Danh sách anime trong test set (sẽ dùng làm ground truth)
            test_anime_ids = set(test_ratings['anime_id'])

            try:
                # Tính profile người dùng chỉ từ dữ liệu train
                # Lưu bản sao của animelist_df hiện tại
                orig_animelist_df = self.animelist_df

                # Tạm thời thay thế bằng train data để tính profile
                self.animelist_df = train_ratings

                # Xóa cache user profile nếu có
                if user_id in self.user_profiles:
                    del self.user_profiles[user_id]

                # Tính profile người dùng từ train data
                user_profile = self.calculate_user_profile(user_id)

                # Khôi phục animelist_df
                self.animelist_df = orig_animelist_df

                # Dự đoán điểm cho tất cả anime
                predicted_scores = self.anime_genre_matrix.dot(user_profile)

                # Tạo mask để loại bỏ anime trong train set (chỉ xét anime chưa thấy trong train)
                train_anime_ids = set(train_ratings['anime_id'])
                mask = np.ones(len(predicted_scores), dtype=bool)
                for anime_id in train_anime_ids:
                    if anime_id in self.anime_id_map:
                        mask[self.anime_id_map[anime_id]] = False

                # Áp dụng mask
                filtered_scores = predicted_scores[mask]
                filtered_indices = np.arange(len(predicted_scores))[mask]

                # Nếu không còn anime nào sau khi lọc, bỏ qua user này
                if len(filtered_scores) == 0:
                    continue

                # Sắp xếp và lấy top-k lớn nhất
                max_k = max(k_values)
                top_k = min(max_k, len(filtered_scores))
                top_k_indices = np.argsort(-filtered_scores)[:top_k]

                # Lấy anime_ids được đề xuất
                recommended_indices = filtered_indices[top_k_indices]
                recommended_ids = [self.reverse_anime_id_map[idx] for idx in recommended_indices]

                # Cập nhật set anime đã đề xuất
                recommended_anime_ids.update(recommended_ids)

                # Nếu có ít nhất một đề xuất, tăng counter
                if len(recommended_ids) > 0:
                    users_with_recommendations += 1

                # Tính metrics cho từng k
                for k in k_values:
                    actual_k = min(k, len(recommended_ids))
                    recommended_k = recommended_ids[:actual_k]

                    # Tính precision@k
                    hits_k = len(set(recommended_k) & test_anime_ids)
                    precision_k = hits_k / actual_k if actual_k > 0 else 0
                    metrics['precision'][k].append(precision_k)

                    # Tính recall@k
                    recall_k = hits_k / len(test_anime_ids) if len(test_anime_ids) > 0 else 0
                    metrics['recall'][k].append(recall_k)

                    # Tính NDCG@k
                    dcg_k = 0
                    idcg_k = 0

                    # Tính DCG
                    for i, item_id in enumerate(recommended_k):
                        if item_id in test_anime_ids:
                            # Sử dụng công thức: rel_i / log2(i+2)
                            dcg_k += 1 / np.log2(i + 2)

                    # Tính IDCG (Ideal DCG)
                    for i in range(min(actual_k, len(test_anime_ids))):
                        idcg_k += 1 / np.log2(i + 2)

                    # NDCG = DCG / IDCG
                    ndcg_k = dcg_k / idcg_k if idcg_k > 0 else 0
                    metrics['ndcg'][k].append(ndcg_k)

                # Tính Hit Rate và Mean Reciprocal Rank
                hit = False
                reciprocal_rank = 0

                for i, item_id in enumerate(recommended_ids):
                    if item_id in test_anime_ids:
                        hit = True
                        reciprocal_rank = 1 / (i + 1)  # Vị trí bắt đầu từ 1
                        break

                metrics['hit_rate'].append(1 if hit else 0)
                metrics['mean_reciprocal_rank'].append(reciprocal_rank)

                # Tăng counter người dùng đã đánh giá thành công
                metrics['user_count'] += 1

            except Exception as e:
                print(f"Lỗi khi đánh giá cho user {user_id}: {e}")

        # Tính giá trị trung bình cho các metrics
        for k in k_values:
            if metrics['precision'][k]:
                metrics['precision'][k] = sum(metrics['precision'][k]) / len(metrics['precision'][k])
            else:
                metrics['precision'][k] = 0

            if metrics['recall'][k]:
                metrics['recall'][k] = sum(metrics['recall'][k]) / len(metrics['recall'][k])
            else:
                metrics['recall'][k] = 0

            if metrics['ndcg'][k]:
                metrics['ndcg'][k] = sum(metrics['ndcg'][k]) / len(metrics['ndcg'][k])
            else:
                metrics['ndcg'][k] = 0

        if metrics['hit_rate']:
            metrics['hit_rate'] = sum(metrics['hit_rate']) / len(metrics['hit_rate'])
        else:
            metrics['hit_rate'] = 0

        if metrics['mean_reciprocal_rank']:
            metrics['mean_reciprocal_rank'] = sum(metrics['mean_reciprocal_rank']) / len(
                metrics['mean_reciprocal_rank'])
        else:
            metrics['mean_reciprocal_rank'] = 0

        # Tính Catalog Coverage
        metrics['catalog_coverage'] = len(recommended_anime_ids) / len(all_anime_ids) if all_anime_ids else 0

        # Tính Prediction Coverage
        metrics['prediction_coverage'] = users_with_recommendations / len(eval_users) if eval_users.size > 0 else 0

        # Hiển thị kết quả
        print("\nKết quả đánh giá:")
        print(f"Số người dùng đánh giá: {metrics['user_count']}")

        for k in k_values:
            print(f"Precision@{k}: {metrics['precision'][k]:.4f}")
            print(f"Recall@{k}: {metrics['recall'][k]:.4f}")
            print(f"NDCG@{k}: {metrics['ndcg'][k]:.4f}")

        print(f"Hit Rate: {metrics['hit_rate']:.4f}")
        print(f"Mean Reciprocal Rank: {metrics['mean_reciprocal_rank']:.4f}")
        print(f"Catalog Coverage: {metrics['catalog_coverage']:.4f}")
        print(f"Prediction Coverage: {metrics['prediction_coverage']:.4f}")

        print(f"Thời gian đánh giá: {time.time() - start_time:.2f} giây")

        return metrics


# Phần tiện ích có thể sử dụng từ dòng lệnh hoặc notebook
def setup_and_recommend(anime_path, animelist_path, user_id, top_n=10, force_rebuild=False):
    """
    Hàm tiện ích để thiết lập và chạy toàn bộ hệ thống.

    Args:
        anime_path: Đường dẫn đến file anime.csv
        animelist_path: Đường dẫn đến file animelist.csv
        user_id: ID người dùng cần đề xuất
        top_n: Số lượng đề xuất
        force_rebuild: Xây dựng lại model từ đầu

    Returns:
        tuple: (DataFrame chứa đề xuất, đối tượng ContentBase)
    """
    print(f"Thiết lập hệ thống đề xuất anime cho user {user_id}...")

    recommender = ContentBase()

    # Tải dữ liệu tiền xử lý nếu có
    if not recommender.load_preprocessed_data() or force_rebuild:
        # Nếu không có hoặc cần xây dựng lại
        recommender.preprocess_data(anime_path)

    # Đọc và xử lý dữ liệu người dùng
    animelist_df = pd.read_csv(animelist_path)
    recommender.process_user_data(animelist_df, force_rebuild)

    # Đề xuất anime
    recommendations = recommender.recommend(user_id, top_n)

    return recommendations, recommender