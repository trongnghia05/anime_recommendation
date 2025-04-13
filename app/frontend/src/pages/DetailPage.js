import React, { useState, useEffect } from 'react';
import AnimeCard from '../components/AnimeCard';
import { FALLBACK_IMAGE } from '../constants/Images';

const API_ENDPOINTS = {
  ANIME_DETAILS: 'http://localhost:8000/anime',
  SIMILAR_ANIME: 'http://localhost:8000/recommend/similar'
};

const DetailPage = ({ anime, navigateTo, userId }) => {
  const [state, setState] = useState({
    animeDetails: null,
    similarAnimes: [],
    loading: true
  });

  useEffect(() => {
    fetchAnimeData();
  }, [anime, userId]);

  const fetchAnimeData = async () => {
    try {
      const animeIdToFetch = anime?.id || 100;

      // Fetch thông tin chi tiết anime
      const animeDetails = await fetchAnimeDetails(animeIdToFetch);

      // Fetch anime tương tự
      const similarAnimes = await fetchSimilarAnimes(animeIdToFetch);

      setState({
        animeDetails: animeDetails,
        similarAnimes: similarAnimes,
        loading: false
      });
    } catch (error) {
      console.error("Lỗi khi tải dữ liệu anime:", error);
      setState(prevState => ({ ...prevState, loading: false }));
    }
  };

  // Lấy thông tin chi tiết của anime từ API
  const fetchAnimeDetails = async (animeId) => {
    try {
      const response = await fetch(`${API_ENDPOINTS.ANIME_DETAILS}/${animeId}`);

      if (!response.ok) {
        throw new Error('Không thể tải thông tin chi tiết anime');
      }

      const animeData = await response.json();

      return {
        id: animeData.id,
        title: animeData.title || 'Shin Cậu bé bút chì',
        image: animeData.image || FALLBACK_IMAGE,
        description: animeData.description || 'Shin là cậu bé 5 tuổi sống cùng bố mẹ tại thành phố Kasukabe. Cậu bé này nổi tiếng với những trò nghịch ngợm và sự hài hước...',
        rating: animeData.rating || 4.8,
        year: animeData.year || 2021,
        episodes: animeData.episodes || 42,
        status: animeData.status || 'Đang phát sóng',
        genres: animeData.genres || ['Hài hước', 'Đời thường', 'Học đường'],
        studio: animeData.studio || 'Shin-Ei Animation'
      };
    } catch (error) {
      console.error("Lỗi khi tải thông tin chi tiết anime:", error);
      // Trả về dữ liệu mẫu khi API lỗi
      return getFallbackAnimeDetails(animeId);
    }
  };

  // Lấy danh sách anime tương tự từ API
  const fetchSimilarAnimes = async (animeId) => {
    try {
      const response = await fetch(`${API_ENDPOINTS.SIMILAR_ANIME}/${animeId}`);

      if (!response.ok) {
        throw new Error('Không thể tải danh sách anime tương tự');
      }

      const data = await response.json();

      return data.similar_anime.map(item => ({
        id: item.anime_id.toString(),
        title: item.title,
        image: FALLBACK_IMAGE,
        rank: item.rank,
        score: item.score,
        prediction: item.prediction,
        explanation: item.explanation
      }));
    } catch (error) {
      console.error("Lỗi khi tải danh sách anime tương tự:", error);
      // Trả về dữ liệu mẫu khi API lỗi
      return getFallbackSimilarAnimes();
    }
  };

  // Dữ liệu mẫu cho thông tin chi tiết anime
  const getFallbackAnimeDetails = (animeId) => {
    return {
      id: animeId || 'default-1',
      title: anime?.title || 'Shin Cậu bé bút chì',
      image: anime?.image || FALLBACK_IMAGE,
      description: 'Shin là cậu bé 5 tuổi sống cùng bố mẹ tại thành phố Kasukabe. Cậu bé này nổi tiếng với những trò nghịch ngợm và sự hài hước. Shin luôn khiến mọi người xung quanh phát điên vì những trò đùa và hành động của mình. Tuy nhiên, cậu cũng là một đứa trẻ rất chân thành và đáng yêu.',
      rating: 4.8,
      year: 2021,
      episodes: 42,
      status: 'Đang phát sóng',
      genres: ['Hài hước', 'Đời thường', 'Học đường'],
      studio: 'Shin-Ei Animation'
    };
  };

  // Dữ liệu mẫu cho danh sách anime tương tự
  const getFallbackSimilarAnimes = () => {
    return [
      {
        id: 'similar-1',
        title: 'Doraemon',
        image: FALLBACK_IMAGE,
        rank: 1,
        score: 4.7,
        prediction: 95
      },
      {
        id: 'similar-2',
        title: 'Chibi Maruko-chan',
        image: FALLBACK_IMAGE,
        rank: 2,
        score: 4.5,
        prediction: 90
      },
      {
        id: 'similar-3',
        title: 'Atashin\'chi',
        image: FALLBACK_IMAGE,
        rank: 3,
        score: 4.3,
        prediction: 85
      },
      {
        id: 'similar-4',
        title: 'Kiteretsu',
        image: FALLBACK_IMAGE,
        rank: 4,
        score: 4.2,
        prediction: 80
      }
    ];
  };

  if (state.loading || !state.animeDetails) {
    return <div className="text-center py-10">Đang tải thông tin anime...</div>;
  }

  return (
    <div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
        {/* Anime Image */}
        <div className="md:col-span-1">
          <div className="rounded-lg overflow-hidden">
            <img
              src={state.animeDetails.image}
              alt={state.animeDetails.title}
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
          <h1 className="text-2xl font-bold mb-3">{state.animeDetails.title}</h1>

          <div className="flex items-center mb-4">
            <div className="flex items-center text-yellow-500 mr-4">
              <span className="mr-1">⭐</span>
              <span className="font-medium">{state.animeDetails.rating}</span>
            </div>
            <div className="text-gray-600 mr-4">
              {state.animeDetails.year}
            </div>
            <div className="text-gray-600 mr-4">
              {state.animeDetails.episodes} tập
            </div>
            <div className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
              {state.animeDetails.status}
            </div>
          </div>

          <p className="text-gray-700 mb-6">
            {state.animeDetails.description}
          </p>

          <div className="mb-4">
            <h3 className="font-medium mb-2">Thể loại:</h3>
            <div className="flex flex-wrap gap-2">
              {state.animeDetails.genres.map(genre => (
                <span key={genre} className="px-3 py-1 bg-gray-200 text-gray-800 text-sm rounded-full">
                  {genre}
                </span>
              ))}
            </div>
          </div>

          <div className="mb-4">
            <h3 className="font-medium mb-2">Studio:</h3>
            <span className="text-gray-700">{state.animeDetails.studio}</span>
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
          {state.similarAnimes.map(anime => (
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