import React from 'react';
import { FALLBACK_IMAGE } from '../constants/Images';

const AnimeCard = ({ anime, navigateTo }) => {
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
        {anime.episodeNumber && (
          <div className="absolute bottom-0 right-0 bg-black bg-opacity-70 text-white text-xs px-2 py-1 rounded-tl-md">
            Tập {anime.episodeNumber}
          </div>
        )}
      </div>
      <h3 className="mt-2 text-sm font-medium truncate">{anime.title}</h3>
      {anime.updatedAt && (
        <p className="text-xs text-gray-500">{anime.updatedAt}</p>
      )}
    </div>
  );
};

export default AnimeCard;