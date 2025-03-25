import React, { useState } from 'react';
import Header from './components/Header';
import Footer from './components/Footer';
import HomePage from './pages/HomePage';
import SearchPage from './pages/SearchPage';
import RankingPage from './pages/RankingPage';
import DetailPage from './pages/DetailPage';

const App = () => {
  const [currentPage, setCurrentPage] = useState('home');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedAnime, setSelectedAnime] = useState(null);
  const [userId, setUserId] = useState('user123'); // user ID mặc định

  // Thay đổi page handler
  const navigateTo = (page, anime = null) => {
    setCurrentPage(page);
    if (anime) setSelectedAnime(anime);
    window.scrollTo(0, 0);
  };

  return (
    <div className="flex flex-col min-h-screen bg-gray-100">
      <Header
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        userId={userId}
        setUserId={setUserId}
        navigateTo={navigateTo}
      />
      <main className="flex-grow container mx-auto px-4 py-6">
        {currentPage === 'home' && <HomePage navigateTo={navigateTo} userId={userId} />}
        {currentPage === 'search' && <SearchPage query={searchQuery} navigateTo={navigateTo} userId={userId} />}
        {currentPage === 'ranking' && <RankingPage navigateTo={navigateTo} userId={userId} />}
        {currentPage === 'detail' && <DetailPage anime={selectedAnime} navigateTo={navigateTo} userId={userId} />}
      </main>
      <Footer />
    </div>
  );
};

export default App;