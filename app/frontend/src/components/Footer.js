import React from 'react';

const Footer = () => {
  return (
    <footer className="bg-gray-800 text-white py-8">
      <div className="container mx-auto px-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div>
            <h3 className="text-lg font-bold mb-4">AnimeTV</h3>
            <p className="text-gray-400">Trang web xem anime trực tuyến với hàng ngàn bộ anime chất lượng cao.</p>
          </div>

          <div>
            <h3 className="text-lg font-bold mb-4">Danh mục</h3>
            <ul className="space-y-2">
              <li><a href="#" className="text-gray-400 hover:text-white">Phim mới</a></li>
              <li><a href="#" className="text-gray-400 hover:text-white">Phổ biến</a></li>
              <li><a href="#" className="text-gray-400 hover:text-white">Xếp hạng</a></li>
              <li><a href="#" className="text-gray-400 hover:text-white">Thể loại</a></li>
            </ul>
          </div>

          <div>
            <h3 className="text-lg font-bold mb-4">Hỗ trợ</h3>
            <ul className="space-y-2">
              <li><a href="#" className="text-gray-400 hover:text-white">Trung tâm trợ giúp</a></li>
              <li><a href="#" className="text-gray-400 hover:text-white">FAQ</a></li>
              <li><a href="#" className="text-gray-400 hover:text-white">Liên hệ</a></li>
              <li><a href="#" className="text-gray-400 hover:text-white">Điều khoản sử dụng</a></li>
            </ul>
          </div>

          <div>
            <h3 className="text-lg font-bold mb-4">Theo dõi chúng tôi</h3>
            <div className="flex space-x-4">
              <a href="#" className="text-gray-400 hover:text-white">
                Facebook
              </a>
              <a href="#" className="text-gray-400 hover:text-white">
                Twitter
              </a>
              <a href="#" className="text-gray-400 hover:text-white">
                Instagram
              </a>
            </div>
          </div>
        </div>

        <div className="mt-8 pt-6 border-t border-gray-700 text-center text-gray-400">
          <p>© 2025 AnimeTV. Tất cả các quyền được bảo lưu.</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;