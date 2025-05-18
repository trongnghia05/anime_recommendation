import React from 'react';
import { FALLBACK_IMAGE } from '../constants/Images';

const AnimeCard = ({ anime, navigateTo }) => {
  // Render rating stars - chức năng mới được thêm vào
  const renderStars = (rating) => {
    // Đảm bảo rating là số hợp lệ từ 0-5
    console.log('Rating value:', anime.rating, typeof anime.rating);
    const validRating = Math.max(0, Math.min( Number(rating) || 0));
    const fullStars = Math.floor(validRating);
    const hasHalfStar = validRating % 1 >= 0.5;
    const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);
    return (
      <div className="flex items-center">
        {/* Full stars */}
        {Array.from({ length: fullStars }, (_, i) => (
          <svg key={`full-${i}`} className="w-3 h-3 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"></path>
          </svg>
        ))}

        {/* Half star */}
        {hasHalfStar && (
          <div className="relative w-3 h-3">
            {/* Gray background star */}
            <svg className="absolute w-3 h-3 text-gray-300" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"></path>
            </svg>
            {/* Half yellow star with clipPath */}
            <svg className="absolute w-3 h-3 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
              <defs>
                <clipPath id={`halfStar-${anime.id || 'default'}`}>
                  <rect x="0" y="0" width="10" height="20" />
                </clipPath>
              </defs>
              <path
                clipPath={`url(#halfStar-${anime.id || 'default'})`}
                d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"
              />
            </svg>
          </div>
        )}

        {/* Empty stars */}
        {Array.from({ length: emptyStars }, (_, i) => (
          <svg key={`empty-${i}`} className="w-3 h-3 text-gray-300" fill="currentColor" viewBox="0 0 20 20">
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"></path>
          </svg>
        ))}

        {/* Rating số */}
        <span className="ml-1 text-xs text-gray-600">{validRating.toFixed(1)}</span>
      </div>
    );
  };

  // Giữ nguyên code cũ
  return (
    <div
      className="cursor-pointer transition-transform duration-200 hover:scale-105"
      onClick={() => navigateTo('detail', anime)}
    >
      <div className="relative pb-[133%] overflow-hidden rounded-md bg-gray-200">
        <img
          src={anime.image || FALLBACK_IMAGE}
          alt={anime.title}
          className="absolute top-0 left-0 w-full h-full object-cover"
          onError={(e) => {
            e.target.onerror = null;
            e.target.src = FALLBACK_IMAGE;
          }}
        />
        {anime.viewCount && (
          <div className="absolute top-0 right-0 bg-black bg-opacity-70 text-white text-xs px-2 py-1 rounded-bl-md flex items-center">
            {/* Icon mắt - giữ nguyên như code hiện tại */}
            <svg
              className="w-3 h-3 mr-1"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M12 4.5C7 4.5 2.73 7.61 1 12C2.73 16.39 7 19.5 12 19.5C17 19.5 21.27 16.39 23 12C21.27 7.61 17 4.5 12 4.5ZM12 17C9.24 17 7 14.76 7 12C7 9.24 9.24 7 12 7C14.76 7 17 9.24 17 12C17 14.76 14.76 17 12 17ZM12 9C10.34 9 9 10.34 9 12C9 13.66 10.34 15 12 15C13.66 15 15 13.66 15 12C15 10.34 13.66 9 12 9Z"
                fill="currentColor"
              />
            </svg>
            {anime.viewCount} lượt xem
          </div>
        )}
        {anime.episodeNumber && (
          <div className="absolute bottom-0 right-0 bg-black bg-opacity-70 text-white text-xs px-2 py-1 rounded-tl-md">
            Tập {anime.episodeNumber}
          </div>
        )}
      </div>

      {/* Giữ nguyên phần hiển thị tiêu đề */}
      <h3 className="mt-2 text-sm font-medium truncate">{anime.title}</h3>
      {/* PHẦN MỚI: Thêm rating stars (chỉ hiển thị nếu có rating) */}
      {anime.rating !== undefined && anime.rating !== null && (
        <div className="mt-1">
          {renderStars(anime.rating)}
        </div>
      )}

      {/* Giữ nguyên phần hiển thị updatedAt */}
      {anime.updatedAt && (
        <p className="text-xs text-gray-500 mt-1">{anime.updatedAt}</p>
      )}
    </div>
  );
};

export default AnimeCard;