import React, { useState, useEffect } from 'react';
import AnimeSection from '../components/AnimeSection';
import { FALLBACK_IMAGE } from '../constants/Images';

const HomePage = ({ navigateTo, userId }) => {
  const [continueWatching, setContinueWatching] = useState([]);
  const [trending, setTrending] = useState([]);
  const [topRated, setTopRated] = useState([]);
  const [recommended, setRecommended] = useState([]);
  const [loading, setLoading] = useState(true);

  // Giả lập gọi API
  useEffect(() => {
    // Khi làm, gọi API ở đây
    const fetchHomePageData = async () => {
      try {
        // Hiện tại để demo, sử dụng link ảnh giả
        setContinueWatching([
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
        ]);

        setTrending([
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
        ]);

        setTopRated([
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
        ]);

        setRecommended([
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
        ]);

        setLoading(false);
      } catch (error) {
        console.error("Lỗi khi tải dữ liệu trang chủ:", error);
        setLoading(false);
      }
    };

    fetchHomePageData();
  }, [userId]);

  if (loading) {
    return <div className="text-center py-10">Đang tải dữ liệu...</div>;
  }

  return (
    <div>
      <AnimeSection
        title="Tiếp tục xem"
        animes={continueWatching}
        navigateTo={navigateTo}
        icon="🕒"
      />
      <AnimeSection
        title="Đang thịnh hành"
        animes={trending}
        navigateTo={navigateTo}
        icon="🔥"
      />
      <AnimeSection
        title="Đánh giá cao"
        animes={topRated}
        navigateTo={navigateTo}
        icon="⭐"
      />
      <AnimeSection
        title="Đề xuất cho bạn"
        animes={recommended}
        navigateTo={navigateTo}
      />
    </div>
  );
};

export default HomePage;