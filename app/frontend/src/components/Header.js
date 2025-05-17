import React, { useState, useEffect } from 'react';
import { Search } from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000'; // API base URL
const RECOMMENDATION_API_URL = 'http://localhost:5000/recommend';

// Mock data for suggestion fallback
const MOCK_SUGGESTIONS = [
  { id: 1, title: 'Shin Cậu bé bút chì' },
  { id: 2, title: 'Shin và những người bạn' },
  { id: 3, title: 'Shin: Cuộc phiêu lưu mới' },
  { id: 4, title: 'Shin và gia đình' }
];

const Header = ({ searchQuery, setSearchQuery, userId, setUserId, navigateTo }) => {
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [useApiSearch, setUseApiSearch] = useState(true); // Toggle between API and mock data
  const [hasClickedSearchBox, setHasClickedSearchBox] = useState(false);

  // Function to load mock suggestions (renamed to avoid "use" prefix)
  const loadMockSuggestions = () => {
    console.log(`Fetching mock suggestions for user: ${userId}`);
    setSuggestions(MOCK_SUGGESTIONS);
    setLoading(false);
  };

  // Fetch recommendations when the search box is clicked
  useEffect(() => {
    if (hasClickedSearchBox) {
      const fetchRecommendations = async () => {
        setLoading(true);
        try {
          const response = await fetch(
            `${RECOMMENDATION_API_URL}?user_id=${userId}&include_metadata=true`
          );
          if (response.ok) {
            const data = await response.json();
            // Assuming the API returns an array of recommendations with a 'title' property
            const formattedRecommendations = data.map((item, index) => ({
              id: item.id || index + 1, // Adjust based on your API response
              title: item.title || "Recommended Item" // Adjust based on your API response
            }));
            setSuggestions(formattedRecommendations);
          } else {
            console.error('Error fetching recommendations:', response.statusText);
            setTimeout(loadMockSuggestions, 300);
          }
        } catch (error) {
          console.error('Failed to fetch recommendations:', error);
          setTimeout(loadMockSuggestions, 300);
        } finally {
          setLoading(false);
        }
      };

      fetchRecommendations();
      setHasClickedSearchBox(false); // Reset the flag after fetching
    }
  }, [userId, hasClickedSearchBox]);

  // Fetch search suggestions from API or use mock data based on search query
  useEffect(() => {
    if (!hasClickedSearchBox && searchQuery.trim().length > 0) {
      setSuggestions([]);
      setLoading(true);

      let timeoutId;

      if (useApiSearch) {
        const fetchSearchSuggestions = async () => {
          try {
            const response = await fetch(
              `${API_BASE_URL}/search/suggestions?q=${encodeURIComponent(searchQuery)}&limit=5`
            );

            if (response.ok) {
              const data = await response.json();
              const formattedSuggestions = data.suggestions.map((item, index) => ({
                id: item.MAL_ID.toString() || index + 1,
                title: item.Name || "Unknown"
              }));
              setSuggestions(formattedSuggestions);
            } else {
              console.error('Error fetching search suggestions:', response.statusText);
              setTimeout(loadMockSuggestions, 300);
            }
          } catch (error) {
            console.error('Failed to fetch search suggestions:', error);
            setTimeout(loadMockSuggestions, 300);
          } finally {
            setLoading(false);
          }
        };

        timeoutId = setTimeout(fetchSearchSuggestions, 300);
      } else {
        timeoutId = setTimeout(loadMockSuggestions, 300);
      }

      return () => {
        if (timeoutId) {
          clearTimeout(timeoutId);
        }
      };
    } else if (!hasClickedSearchBox && searchQuery.trim().length === 0) {
      setSuggestions([]);
      setLoading(false);
    }
  }, [searchQuery, userId, useApiSearch, hasClickedSearchBox]);

  const handleSearch = (e) => {
    e.preventDefault();
    navigateTo('search');
    setShowSuggestions(false);
  };

  const handleSearchBoxClick = () => {
    setShowSuggestions(true);
    setHasClickedSearchBox(true);
    setSearchQuery(''); // Clear the search query when the box is clicked
  };

  // Function to toggle between API and mock data (for testing)
  const toggleApiSearch = () => {
    setUseApiSearch(!useApiSearch);
  };

  return (
    <header className="bg-white shadow">
      <div className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-between">
          <div
            className="text-2xl font-bold text-blue-600 cursor-pointer"
            onClick={() => navigateTo('home')}
          >
            AnimeTV
          </div>

          <div className="flex items-center w-full max-w-xl mx-6">
            <div className="relative flex-grow mr-2">
              <form onSubmit={handleSearch} className="relative">
                <input
                  type="text"
                  placeholder="Tìm kiếm anime..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onFocus={handleSearchBoxClick}
                  className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button type="submit" className="absolute left-3 top-2.5 text-gray-500">
                  <Search size={18} />
                </button>
              </form>

              {showSuggestions && (
                <div className="absolute z-10 w-full mt-1 bg-white border rounded-lg shadow-lg">
                  {loading ? (
                    <div className="p-3 text-gray-500 text-center">Đang tải gợi ý...</div>
                  ) : (
                    <>
                      {suggestions.length > 0 ? (
                        <ul>
                          {suggestions.map(suggestion => (
                            <li
                              key={suggestion.id}
                              className="px-4 py-2 hover:bg-gray-100 cursor-pointer"
                              onClick={() => {
                                setSearchQuery(suggestion.title);
                                navigateTo('search');
                                setShowSuggestions(false);
                              }}
                            >
                              {suggestion.title}
                            </li>
                          ))}
                        </ul>
                      ) : !hasClickedSearchBox && searchQuery.trim().length > 0 ? (
                        <div className="p-3 text-gray-500 text-center">Không tìm thấy kết quả</div>
                      ) : hasClickedSearchBox && suggestions.length === 0 ? (
                        <div className="p-3 text-gray-500 text-center">Không có gợi ý</div>
                      ) : null}
                    </>
                  )}
                </div>
              )}
            </div>

            <div className="w-32">
              <div className="relative">
                <input
                  type="text"
                  placeholder="User ID"
                  value={userId}
                  onChange={(e) => setUserId(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                />
              </div>
            </div>
          </div>

          <nav>
            <ul className="flex space-x-6">
              <li>
                <button
                  onClick={() => navigateTo('ranking')}
                  className="text-gray-700 hover:text-blue-600"
                >
                  Xếp hạng
                </button>
              </li>
              <li>
                <button className="text-gray-700 hover:text-blue-600">
                  Mới cập nhật
                </button>
              </li>
              <li>
                {/* Hidden in production - for testing only */}
                <button
                  onClick={toggleApiSearch}
                  className="text-xs text-gray-400 hover:text-blue-600"
                  title={useApiSearch ? "Đang dùng API thật" : "Đang dùng dữ liệu giả lập"}
                >
                  {useApiSearch ? "API" : "Mock"}
                </button>
              </li>
            </ul>
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header;