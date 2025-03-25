import React from 'react';
import AnimeCard from './AnimeCard';

const AnimeSection = ({ title, animes, navigateTo, icon }) => {
  return (
    <section className="mb-8">
      <div className="flex items-center mb-4">
        <h2 className="text-xl font-bold">{title}</h2>
        {icon && <span className="ml-2">{icon}</span>}
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
        {animes.map(anime => (
          <AnimeCard key={anime.id} anime={anime} navigateTo={navigateTo} />
        ))}
      </div>
    </section>
  );
};

export default AnimeSection;