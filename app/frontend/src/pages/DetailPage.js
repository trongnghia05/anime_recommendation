import React, { useState, useEffect } from 'react';
import AnimeCard from '../components/AnimeCard';
import { FALLBACK_IMAGE } from '../constants/Images';

const DetailPage = ({ anime, navigateTo, userId }) => {
  const [animeDetails, setAnimeDetails] = useState(null);
  const [similarAnimes, setSimilarAnimes] = useState([]);
  const [loading, setLoading] = useState(true);

  // Giả lập gọi API chi tiết anime và fetch đề xuất từ API thật
  useEffect(() => {
    const fetchAnimeDetails = async () => {
      try {
        // Dữ liệu giả lập - trong thực tế sẽ nhận từ API
        let details;

        if (!anime) {
          // Default anime nếu không có anime được chọn
          details = {
            id: 'default-1',
            title: 'Shin Cậu bé bút chì',
            image: FALLBACK_IMAGE,
            description: 'Shin là cậu bé 5 tuổi sống cùng bố mẹ tại thành phố Kasukabe. Cậu bé này nổi tiếng với những trò nghịch ngợm và sự hài hước. Shin luôn khiến mọi người xung quanh phát điên vì những trò đùa và hành động của mình. Tuy nhiên, cậu cũng là một đứa trẻ rất chân thành và đáng yêu.',
            rating: 4.8,
            year: 2021,
            episodes: 42,
            status: 'Đang phát sóng',
            genres: ['Hài hước', 'Đời thường', 'Học đường'],
            studio: 'Shin-Ei Animation'
          };
        } else {
          // Tạo thông tin dựa trên anime được chọn
          details = {
            id: anime.id,
            title: anime.title || 'Shin Cậu bé bút chì',
            image: anime.image || FALLBACK_IMAGE, // Ưu tiên dùng ảnh từ anime được chọn
            description: 'Shin là cậu bé 5 tuổi sống cùng bố mẹ tại thành phố Kasukabe. Cậu bé này nổi tiếng với những trò nghịch ngợm và sự hài hước. Shin luôn khiến mọi người xung quanh phát điên vì những trò đùa và hành động của mình. Tuy nhiên, cậu cũng là một đứa trẻ rất chân thành và đáng yêu.',
            rating: 4.8,
            year: 2021,
            episodes: 42,
            status: 'Đang phát sóng',
            genres: ['Hài hước', 'Đời thường', 'Học đường'],
            studio: 'Shin-Ei Animation'
          };
        }

        setAnimeDetails(details);

        // Fetch đề xuất anime từ API thật
        try {
          const userIdToFetch = userId || 100; // Sử dụng ID người dùng được truyền hoặc mặc định là 100
          const response = await fetch(`http://localhost:8000/recommend/${userIdToFetch}`);

          if (!response.ok) {
            throw new Error('Không thể tải dữ liệu đề xuất');
          }

          const recommendData = await response.json();
          console.log(recommendData)
          // Chuyển đổi dữ liệu từ API thành định dạng tương thích với component
          const similar = recommendData.recommendations.map(item => ({
            id: item.anime_id.toString(),
            title: item.name,
            image: FALLBACK_IMAGE,
            // rank: item.rank,
            // score: item.score,
            // prediction: item.prediction,
            // explanation: item.explanation
          }));

          setSimilarAnimes(similar);
        } catch (error) {
          console.error("Lỗi khi tải đề xuất anime:", error);
          // Sử dụng dữ liệu giả lập nếu API không hoạt động
          const similar = [
            {
              id: 'similar-1',
              title: 'Doraemon',
              image: FALLBACK_IMAGE
            },
            {
              id: 'similar-2',
              title: 'Chibi Maruko-chan',
              image: FALLBACK_IMAGE
            },
            {
              id: 'similar-3',
              title: 'Atashin\'chi',
              image: FALLBACK_IMAGE
            },
            {
              id: 'similar-4',
              title: 'Kiteretsu',
              image: FALLBACK_IMAGE
            }
          ];
          setSimilarAnimes(similar);
        }

        setLoading(false);
      } catch (error) {
        console.error("Lỗi khi tải thông tin anime:", error);
        setLoading(false);
      }
    };

    fetchAnimeDetails();
  }, [anime, userId]);

  if (loading || !animeDetails) {
    return <div className="text-center py-10">Đang tải thông tin anime...</div>;
  }

  return (
    <div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
        {/* Anime Image */}
        <div className="md:col-span-1">
          <div className="rounded-lg overflow-hidden">
            <img
              src={animeDetails.image}
              alt={animeDetails.title}
              className="w-full h-full object-cover"
              onError={(e) => {
                e.target.onerror = null;
                e.target.src = FALLBACK_IMAGE;
              }}
            />
          </div>
        </div>

        {/* Anime Details */}
        <div className="md:col-span-2">
          <h1 className="text-2xl font-bold mb-3">{animeDetails.title}</h1>

          <div className="flex items-center mb-4">
            <div className="flex items-center text-yellow-500 mr-4">
              <span className="mr-1">⭐</span>
              <span className="font-medium">{animeDetails.rating}</span>
            </div>
            <div className="text-gray-600 mr-4">
              {animeDetails.year}
            </div>
            <div className="text-gray-600 mr-4">
              {animeDetails.episodes} tập
            </div>
            <div className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
              {animeDetails.status}
            </div>
          </div>

          <p className="text-gray-700 mb-6">
            {animeDetails.description}
          </p>

          <div className="mb-4">
            <h3 className="font-medium mb-2">Thể loại:</h3>
            <div className="flex flex-wrap gap-2">
              {animeDetails.genres.map(genre => (
                <span key={genre} className="px-3 py-1 bg-gray-200 text-gray-800 text-sm rounded-full">
                  {genre}
                </span>
              ))}
            </div>
          </div>

          <div className="mb-4">
            <h3 className="font-medium mb-2">Studio:</h3>
            <span className="text-gray-700">{animeDetails.studio}</span>
          </div>

          <div className="flex space-x-4 mt-6">
            <button className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors">
              Xem ngay
            </button>
            <button className="px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-100 transition-colors">
              + Thêm vào danh sách
            </button>
          </div>
        </div>
      </div>

      {/* Similar Anime Section */}
      <div className="mt-12">
        <h2 className="text-xl font-bold mb-4">Anime tương tự</h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
          {similarAnimes.map(anime => (
            <div key={anime.id} className="anime-card-container">
              <AnimeCard key={anime.id} anime={anime} navigateTo={navigateTo} />
              {anime.rank && (
                <div className="mt-1 text-xs">
                  <span className="text-yellow-600">⭐ {anime.score}</span>
                  {anime.prediction && (
                    <span className="ml-2 text-blue-600">{Math.round(anime.prediction)}% phù hợp</span>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default DetailPage;