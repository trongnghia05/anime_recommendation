import React, { useState, useEffect } from 'react';
import AnimeCard from '../components/AnimeCard';
import { FALLBACK_IMAGE } from '../constants/Images';

const API_BASE_URL = 'http://localhost:8000'; // API base URL

const SearchPage = ({ query, navigateTo, userId }) => {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [animeGenres, setAnimeGenres] = useState({}); // Lưu trữ quan hệ giữa anime ID và thể loại

  useEffect(() => {
    const fetchSearchResults = async () => {
      setLoading(true);

      try {
        if (query && query.trim() !== '') {
          try {
            const response = await fetch(`${API_BASE_URL}/search/suggestions?q=${encodeURIComponent(query)}&limit=20`);

            if (response.ok) {
              const data = await response.json();

              if (data.suggestions && data.suggestions.length > 0) {
                const uniqueCategories = new Set();
                const genreMap = {};

                const searchResults = data.suggestions.map(item => {
                  if (item.Genres && item.Genres.length > 0) {
                    const genres = item.Genres.map(g => g.toLowerCase());
                    genreMap[item.MAL_ID] = genres;

                    genres.forEach(genre => uniqueCategories.add(genre));
                  }

                  return {
                    id: item.MAL_ID.toString(),
                    title: item.Name,
                    image: FALLBACK_IMAGE,
                    category: item.Genres && item.Genres.length > 0
                      ? item.Genres[0].toLowerCase()
                      : 'unknown'
                  };
                });

                setResults(searchResults);
                setCategories(Array.from(uniqueCategories).sort());
                setAnimeGenres(genreMap);
                setLoading(false);
                return;
              }
            }
          } catch (apiError) {
            console.error("API error:", apiError);
          }
        }

        // Fallback: Sử dụng dữ liệu mẫu
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

        // Mock data cho genreMap với dữ liệu mẫu
        const mockGenreMap = {
          'search-1': ['action', 'adventure'],
          'search-2': ['comedy', 'slice of life'],
          'search-3': ['drama', 'romance'],
          'search-4': ['fantasy', 'magic'],
          'search-5': ['action', 'sci-fi'],
          'search-6': ['comedy', 'school'],
          'search-7': ['drama', 'psychological'],
          'search-8': ['fantasy', 'adventure']
        };

        setResults(searchResults);
        setCategories(['action', 'comedy', 'drama', 'fantasy', 'adventure', 'romance', 'sci-fi', 'slice of life', 'school', 'psychological', 'magic']);
        setAnimeGenres(mockGenreMap);
        setLoading(false);
      } catch (error) {
        console.error("Lỗi khi tìm kiếm:", error);
        setLoading(false);
      }
    };

    fetchSearchResults();
  }, [query, userId]);

  // Cải thiện hàm lọc để kiểm tra anime có thể loại đã chọn không
  const filteredResults = selectedCategory === 'all'
    ? results
    : results.filter(item => {
        // Kiểm tra trong animeGenres
        const genres = animeGenres[item.id];
        if (genres && Array.isArray(genres)) {
          return genres.includes(selectedCategory);
        }
        // Fallback về category nếu không có trong animeGenres
        return item.category === selectedCategory;
      });

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