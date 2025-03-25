import React, { useState, useEffect } from 'react';
import AnimeCard from '../components/AnimeCard';
import { FALLBACK_IMAGE } from '../constants/Images';

const SearchPage = ({ query, navigateTo, userId }) => {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('all');

  // Giả lập gọi API tìm kiếm
  useEffect(() => {
    const fetchSearchResults = async () => {
      try {
        // // Khi làm, gọi API ở đây
        const searchResults = [
          {
            id: 'search-1',
            title: `${query} Anime 1`,
            image: FALLBACK_IMAGE,
            category: 'action'
          },
          {
            id: 'search-2',
            title: `${query} Anime 2`,
            image: FALLBACK_IMAGE,
            category: 'comedy'
          },
          {
            id: 'search-3',
            title: `${query} Anime 3`,
            image: FALLBACK_IMAGE,
            category: 'drama'
          },
          {
            id: 'search-4',
            title: `${query} Anime 4`,
            image: FALLBACK_IMAGE,
            category: 'fantasy'
          },
          {
            id: 'search-5',
            title: `${query} Anime 5`,
            image: FALLBACK_IMAGE,
            category: 'action'
          },
          {
            id: 'search-6',
            title: `${query} Anime 6`,
            image: FALLBACK_IMAGE,
            category: 'comedy'
          },
          {
            id: 'search-7',
            title: `${query} Anime 7`,
            image: FALLBACK_IMAGE,
            category: 'drama'
          },
          {
            id: 'search-8',
            title: `${query} Anime 8`,
            image: FALLBACK_IMAGE,
            category: 'fantasy'
          }
        ];

        setResults(searchResults);
        setCategories(['action', 'comedy', 'drama', 'fantasy']);
        setLoading(false);
      } catch (error) {
        console.error("Lỗi khi tìm kiếm:", error);
        setLoading(false);
      }
    };

    fetchSearchResults();
  }, [query, userId]);

  const filteredResults = selectedCategory === 'all'
    ? results
    : results.filter(item => item.category === selectedCategory);

  if (loading) {
    return <div className="text-center py-10">Đang tìm kiếm "{query}"...</div>;
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-2">Kết quả tìm kiếm: "{query}"</h1>
        <p className="text-gray-600">Tìm thấy {results.length} kết quả</p>

        <div className="mt-4 flex flex-wrap gap-2">
          <button
            className={`px-3 py-1 rounded-full text-sm ${
              selectedCategory === 'all' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-800'
            }`}
            onClick={() => setSelectedCategory('all')}
          >
            Tất cả
          </button>
          {categories.map(category => (
            <button
              key={category}
              className={`px-3 py-1 rounded-full text-sm ${
                selectedCategory === category ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-800'
              }`}
              onClick={() => setSelectedCategory(category)}
            >
              {category.charAt(0).toUpperCase() + category.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
        {filteredResults.map(anime => (
          <AnimeCard key={anime.id} anime={anime} navigateTo={navigateTo} />
        ))}
      </div>
    </div>
  );
};

export default SearchPage;