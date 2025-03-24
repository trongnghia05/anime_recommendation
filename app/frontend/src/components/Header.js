import React, { useState, useEffect } from 'react';
import { Search } from 'lucide-react';

const Header = ({ searchQuery, setSearchQuery, userId, setUserId, navigateTo }) => {
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);

  // Simulate API call for search suggestions
  useEffect(() => {
    if (searchQuery.trim().length > 0) {
      setLoading(true);
      // Mock API call for suggestions (including userId for personalized suggestions)
      setTimeout(() => {
        console.log(`Fetching suggestions for user: ${userId}`);
        // In a real implementation, userId would be sent to the API
        setSuggestions([
          { id: 1, title: 'Shin Cậu bé bút chì' },
          { id: 2, title: 'Shin và những người bạn' },
          { id: 3, title: 'Shin: Cuộc phiêu lưu mới' },
          { id: 4, title: 'Shin và gia đình' }
        ]);
        setLoading(false);
      }, 300);
    } else {
      setSuggestions([]);
    }
  }, [searchQuery, userId]);

  const handleSearch = (e) => {
    e.preventDefault();
    navigateTo('search');
    setShowSuggestions(false);
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
                  onFocus={() => setShowSuggestions(true)}
                  className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button type="submit" className="absolute left-3 top-2.5 text-gray-500">
                  <Search size={18} />
                </button>
              </form>

              {showSuggestions && (
                <div className="absolute z-10 w-full mt-1 bg-white border rounded-lg shadow-lg">
                  {loading ? (
                    <div className="p-3 text-gray-500 text-center">Đang tìm kiếm...</div>
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
                      ) : searchQuery.trim().length > 0 ? (
                        <div className="p-3 text-gray-500 text-center">Không tìm thấy kết quả</div>
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
            </ul>
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header;