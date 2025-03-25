import React, { useState, useEffect } from 'react';
import { FALLBACK_IMAGE } from '../constants/Images';

const RankingPage = ({ navigateTo, userId }) => {
  const [rankings, setRankings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [timeFilter, setTimeFilter] = useState('week');

  // Giả lập gọi API xếp hạng
  useEffect(() => {
    const fetchRankings = async () => {
      try {
        // Khi làm, gọi API ở đây
        const rankingData = [
          {
            id: 'rank-1',
            title: 'Shin Cậu bé bút chì',
            image: FALLBACK_IMAGE,
            rank: 1,
            views: 9800
          },
          {
            id: 'rank-2',
            title: 'Doraemon',
            image: FALLBACK_IMAGE,
            rank: 2,
            views: 9300
          },
          {
            id: 'rank-3',
            title: 'Dragon Ball',
            image: FALLBACK_IMAGE,
            rank: 3,
            views: 8900
          },
          {
            id: 'rank-4',
            title: 'Naruto',
            image: FALLBACK_IMAGE,
            rank: 4,
            views: 8500
          },
          {
            id: 'rank-5',
            title: 'One Piece',
            image: FALLBACK_IMAGE,
            rank: 5,
            views: 8100
          },
          {
            id: 'rank-6',
            title: 'My Hero Academia',
            image: FALLBACK_IMAGE,
            rank: 6,
            views: 7800
          },
          {
            id: 'rank-7',
            title: 'Attack on Titan',
            image: FALLBACK_IMAGE,
            rank: 7,
            views: 7500
          },
          {
            id: 'rank-8',
            title: 'Demon Slayer',
            image: FALLBACK_IMAGE,
            rank: 8,
            views: 7200
          }
        ];

        setRankings(rankingData);
        setLoading(false);
      } catch (error) {
        console.error("Lỗi khi tải bảng xếp hạng:", error);
        setLoading(false);
      }
    };

    fetchRankings();
  }, [timeFilter, userId]);

  if (loading) {
    return <div className="text-center py-10">Đang tải bảng xếp hạng...</div>;
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-2">Bảng xếp hạng anime</h1>

        <div className="mt-4 flex gap-2">
          <button
            className={`px-4 py-2 rounded-md text-sm ${
              timeFilter === 'day' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-800'
            }`}
            onClick={() => setTimeFilter('day')}
          >
            Ngày
          </button>
          <button
            className={`px-4 py-2 rounded-md text-sm ${
              timeFilter === 'week' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-800'
            }`}
            onClick={() => setTimeFilter('week')}
          >
            Tuần
          </button>
          <button
            className={`px-4 py-2 rounded-md text-sm ${
              timeFilter === 'month' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-800'
            }`}
            onClick={() => setTimeFilter('month')}
          >
            Tháng
          </button>
          <button
            className={`px-4 py-2 rounded-md text-sm ${
              timeFilter === 'all' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-800'
            }`}
            onClick={() => setTimeFilter('all')}
          >
            Tất cả
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-6">
        {rankings.map(anime => (
          <div
            key={anime.id}
            className="cursor-pointer transition-transform duration-200 hover:scale-105"
            onClick={() => navigateTo('detail', anime)}
          >
            <div className="relative pb-[133%] overflow-hidden rounded-md bg-gray-200">
              <img
                src={anime.image}
                alt={anime.title}
                className="absolute top-0 left-0 w-full h-full object-cover"
                onError={(e) => {
                  e.target.onerror = null;
                  e.target.src = FALLBACK_IMAGE;
                }}
              />
              <div className="absolute top-0 left-0 bg-blue-600 text-white font-bold py-1 px-3 rounded-br-md">
                #{anime.rank}
              </div>
            </div>
            <h3 className="mt-2 text-sm font-medium truncate">{anime.title}</h3>
            <p className="text-xs text-gray-500">{anime.views.toLocaleString()} lượt xem</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default RankingPage;