import React, { useState, useEffect } from 'react';
import AnimeSection from '../components/AnimeSection';
import { FALLBACK_IMAGE } from '../constants/Images';

const API_ENDPOINTS = {
  CONTINUE_WATCHING: 'http://localhost:8000/recommend/continue_watching',
  TRENDING: 'http://localhost:8000/recommend/trending',
  TOP_RATE: 'http://localhost:8000/recommend/top_rate',
  SEARCH_SUGGESTIONS: 'http://localhost:5000/recommend',
  RECOMMENDED: 'http://localhost:8000/recommend/because_you_watch'
};

const HomePage = ({ navigateTo, userId }) => {
  const [state, setState] = useState({
    continueWatching: [],
    trending: [],
    topRated: [],
    recommended: [],
    loading: true
  });

  useEffect(() => {
    fetchHomePageData();
  }, [userId]);

  const fetchHomePageData = async () => {
    try {
      const userIdToFetch = userId || 100;

      const continueWatchingData = await fetchContinueWatching(userIdToFetch);
      const trendingData = await fetchTrending(userIdToFetch);
      const topRatedData = await fetchTopRate(userIdToFetch);
      const recommendedData = await fetchRecommendedAnimes(userIdToFetch);

      setState({
        continueWatching: continueWatchingData,
        trending: trendingData,
        topRated: topRatedData,
        recommended: recommendedData,
        loading: false
      });
    } catch (error) {
      console.error("Lỗi khi tải dữ liệu trang chủ:", error);
      setState(prevState => ({ ...prevState, loading: false }));
    }
  };

  // Lấy dữ liệu Tiếp tục xem từ API
  const fetchContinueWatching = async (userIdToFetch) => {
    try {
      const response = await fetch(`${API_ENDPOINTS.CONTINUE_WATCHING}/${userIdToFetch}`);

      if (!response.ok) {
        throw new Error('Không thể tải dữ liệu tiếp tục xem');
      }

      const data = await response.json();

      return data.continue_watching.map(item => ({
        id: item.id.toString(),
        title: item.title,
        image: FALLBACK_IMAGE,
        episodeNumber: 1,
        updatedAt: "Vừa xem"
      }));
    } catch (error) {
      console.error("Lỗi khi tải dữ liệu tiếp tục xem:", error);
      return getFallbackContinueWatchingData();
    }
  };

  // Lấy dữ liệu Đang thịnh hành từ API
  const fetchTrending = async (userIdToFetch) => {
    try {
      const response = await fetch(`${API_ENDPOINTS.TRENDING}/${userIdToFetch}`);

      if (!response.ok) {
        throw new Error('Không thể tải dữ liệu đang thịnh hành');
      }

      const data = await response.json();

      return data.trending.map(item => ({
        id: item.id.toString(),
        title: item.title,
        image: FALLBACK_IMAGE,
        viewCount: item.score
      }));
    } catch (error) {
      console.error("Lỗi khi tải dữ liệu đang thịnh hành:", error);
      return getFallbackTrendingData();
    }
  };

  // Lấy dữ liệu Đánh giá cao từ API
  const fetchTopRate = async (userIdToFetch) => {
    try {
      const response = await fetch(`${API_ENDPOINTS.TOP_RATE}/${userIdToFetch}`);

      if (!response.ok) {
        throw new Error('Không thể tải dữ liệu đánh giá cao');
      }

      const data = await response.json();

      return data.top_rate.map(item => ({
        id: item.id.toString(),
        title: item.title,
        image: FALLBACK_IMAGE,
        rating: item.rating
      }));
    } catch (error) {
      console.error("Lỗi khi tải dữ liệu đánh giá cao:", error);
      return getFallbackTopRateData();
    }
  };

  // Lấy dữ liệu đề xuất phim từ API
  const fetchRecommendedAnimes = async (userIdToFetch) => {
    try {
      const response = await fetch(`${API_ENDPOINTS.RECOMMENDED}/${userIdToFetch}`);

      if (!response.ok) {
        throw new Error('Không thể tải dữ liệu đề xuất');
      }

      const data = await response.json();

      return data.recommendations.map(item => ({
        id: item.anime_id.toString(),
        title: item.name,
        image: FALLBACK_IMAGE,
        score: item.score,
        matchPercentage: Math.round(item.prediction),
        explanation: item.explanation
      }));
    } catch (error) {
      console.error("Lỗi khi tải đề xuất anime:", error);
      return getFallbackRecommendedData();
    }
  };

  const fetchSearchSuggestionsOnFocus = async () => {
    try {
      const userIdToFetch = userId || 100;
      const searchUrl = `${API_ENDPOINTS.SEARCH_SUGGESTIONS}?user_id=${userIdToFetch}&include_metadata=true`;
      const response = await fetch(searchUrl);

      if (!response.ok) {
        console.error('Lỗi khi tải gợi ý tìm kiếm');
        return;
      }

      const data = await response.json();
      console.log('Dữ liệu gợi ý tìm kiếm:', data);
    } catch (error) {
      console.error("Lỗi khi tải gợi ý tìm kiếm:", error);
    }
  };

  // Dữ liệu mẫu cho phần Tiếp tục xem khi API lỗi
  const getFallbackContinueWatchingData = () => {
    return [
      {
        id: 'continue-1',
        title: 'Shin Cậu bé bút chì - Tập 1',
        image: FALLBACK_IMAGE,
        episodeNumber: 1,
        updatedAt: "Vừa xem"
      },
      {
        id: 'continue-2',
        title: 'Shin Cậu bé bút chì - Tập 2',
        image: FALLBACK_IMAGE,
        episodeNumber: 2,
        updatedAt: "Vừa xem"
      },
      {
        id: 'continue-3',
        title: 'Shin Cậu bé bút chì - Tập 3',
        image: FALLBACK_IMAGE,
        episodeNumber: 3,
        updatedAt: "Vừa xem"
      },
      {
        id: 'continue-4',
        title: 'Shin Cậu bé bút chì - Tập 4',
        image: FALLBACK_IMAGE,
        episodeNumber: 4,
        updatedAt: "Vừa xem"
      },
      {
        id: 'continue-5',
        title: 'Shin Cậu bé bút chì - Tập 5',
        image: FALLBACK_IMAGE,
        episodeNumber: 5,
        updatedAt: "Vừa xem"
      }
    ];
  };

  // Dữ liệu mẫu cho phần Đang thịnh hành
  const getFallbackTrendingData = () => {
    return [
      {
        id: 'trending-1',
        title: 'Shin Cậu bé bút chì - Phần 1',
        image: FALLBACK_IMAGE,
        viewCount: 950000
      },
      {
        id: 'trending-2',
        title: 'Shin Cậu bé bút chì - Phần 2',
        image: FALLBACK_IMAGE,
        viewCount: 850000
      },
      {
        id: 'trending-3',
        title: 'Shin Cậu bé bút chì - Phần 3',
        image: FALLBACK_IMAGE,
        viewCount: 750000
      },
      {
        id: 'trending-4',
        title: 'Shin Cậu bé bút chì - Phần 4',
        image: FALLBACK_IMAGE,
        viewCount: 650000
      },
      {
        id: 'trending-5',
        title: 'Shin Cậu bé bút chì - Phần 5',
        image: FALLBACK_IMAGE,
        viewCount: 550000
      }
    ];
  };

  // Dữ liệu mẫu cho phần Đánh giá cao
  const getFallbackTopRateData = () => {
    return [
      {
        id: 'toprated-1',
        title: 'Shin và những người bạn 1',
        image: FALLBACK_IMAGE,
        rating: 4.9
      },
      {
        id: 'toprated-2',
        title: 'Shin và những người bạn 2',
        image: FALLBACK_IMAGE,
        rating: 4.8
      },
      {
        id: 'toprated-3',
        title: 'Shin và những người bạn 3',
        image: FALLBACK_IMAGE,
        rating: 4.7
      },
      {
        id: 'toprated-4',
        title: 'Shin và những người bạn 4',
        image: FALLBACK_IMAGE,
        rating: 4.6
      },
      {
        id: 'toprated-5',
        title: 'Shin và những người bạn 5',
        image: FALLBACK_IMAGE,
        rating: 4.5
      }
    ];
  };

  // Dữ liệu mẫu cho phần Đề xuất khi API lỗi
  const getFallbackRecommendedData = () => {
    return [
      {
        id: 'recommended-1',
        title: 'Shin: Phiêu lưu ở 1',
        image: FALLBACK_IMAGE,
        matchPercentage: 99
      },
      {
        id: 'recommended-2',
        title: 'Shin: Phiêu lưu ở 2',
        image: FALLBACK_IMAGE,
        matchPercentage: 98
      },
      {
        id: 'recommended-3',
        title: 'Shin: Phiêu lưu ở 3',
        image: FALLBACK_IMAGE,
        matchPercentage: 97
      },
      {
        id: 'recommended-4',
        title: 'Shin: Phiêu lưu ở 4',
        image: FALLBACK_IMAGE,
        matchPercentage: 96
      },
      {
        id: 'recommended-5',
        title: 'Shin: Phiêu lưu ở 5',
        image: FALLBACK_IMAGE,
        matchPercentage: 95
      }
    ];
  };

  if (state.loading) {
    return <div className="text-center py-10">Đang tải dữ liệu...</div>;
  }

  return (
    <div>
      {/* Example of a search input */}
      <input
        type="text"
        placeholder="Tìm kiếm anime..."
        onFocus={fetchSearchSuggestionsOnFocus}
      />

      <AnimeSection
        title="Tiếp tục xem"
        animes={state.continueWatching}
        navigateTo={navigateTo}
        icon="🕒"
      />
      <AnimeSection
        title="Đang thịnh hành"
        animes={state.trending}
        navigateTo={navigateTo}
        icon="🔥"
      />
      <AnimeSection
        title="Đánh giá cao"
        animes={state.topRated}
        navigateTo={navigateTo}
        icon="⭐"
      />
      <AnimeSection
        title="Có thể bạn sẽ thích"
        animes={state.recommended}
        navigateTo={navigateTo}
        icon="👍"
      />
    </div>
  );
};

export default HomePage;