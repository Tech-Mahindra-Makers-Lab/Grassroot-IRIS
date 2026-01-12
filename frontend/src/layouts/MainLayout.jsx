import React, { useState, useEffect } from 'react';
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom';
import { LayoutDashboard, Bell, FileText, LogOut, PlusCircle, ShieldCheck, MailPlus, Target } from 'lucide-react';
import api from '../api';

const MainLayout = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const userName = localStorage.getItem('iris_user_name') || 'User';
    const userId = localStorage.getItem('iris_user_id');
    const [unreadCount, setUnreadCount] = useState(0);

    const fetchUnreadCount = async () => {
        if (!userId) return;
        try {
            const res = await api.get(`notifications/?user_id=${userId}`);
            const unread = res.data.filter(n => !n.is_read).length;
            setUnreadCount(unread);
        } catch (err) {
            console.error("Polling error:", err);
        }
    };

    useEffect(() => {
        fetchUnreadCount();
        const interval = setInterval(fetchUnreadCount, 30000); // Poll every 30s
        return () => clearInterval(interval);
    }, []);

    const handleLogout = () => {
        localStorage.clear();
        navigate('/login');
    };

    return (
        <div className="flex h-screen bg-gray-50 text-gray-900">
            {/* Sidebar */}
            <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
                <div className="p-6 border-b border-gray-200 flex items-center gap-3">
                    <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold">I</div>
                    <span className="text-xl font-bold text-gray-800">IRIS</span>
                </div>

                <nav className="flex-1 p-4 space-y-2">
                    <Link to="/" className={`flex items-center gap-3 p-3 rounded-lg transition-colors group ${location.pathname === '/' ? 'bg-blue-600 text-white shadow-lg shadow-blue-100' : 'text-gray-700 hover:bg-blue-50 hover:text-blue-600'}`}>
                        <LayoutDashboard size={20} className="group-hover:scale-110 transition-transform" />
                        <span className="font-medium">Dashboard</span>
                    </Link>
                    <Link to="/submit-grassroot" className={`flex items-center gap-3 p-3 rounded-lg transition-colors group ${location.pathname === '/submit-grassroot' ? 'bg-blue-600 text-white shadow-lg shadow-blue-100' : 'text-gray-700 hover:bg-blue-50 hover:text-blue-600'}`}>
                        <PlusCircle size={20} className="group-hover:scale-110 transition-transform" />
                        <span className="font-medium">Submit Idea</span>
                    </Link>
                    <Link to="/post-challenge" className={`flex items-center gap-3 p-3 rounded-lg transition-colors group ${location.pathname === '/post-challenge' ? 'bg-blue-600 text-white shadow-lg shadow-blue-100' : 'text-gray-700 hover:bg-blue-50 hover:text-blue-600'}`}>
                        <Target size={20} className="group-hover:scale-110 transition-transform" />
                        <span className="font-medium">Post Challenge</span>
                    </Link>
                    <Link to="/management" className={`flex items-center gap-3 p-3 rounded-lg transition-colors group ${location.pathname === '/management' ? 'bg-blue-600 text-white shadow-lg shadow-blue-100' : 'text-gray-700 hover:bg-blue-50 hover:text-blue-600'}`}>
                        <ShieldCheck size={20} className="group-hover:scale-110 transition-transform" />
                        <span className="font-medium">Management</span>
                    </Link>
                    <Link to="/notifications" className={`flex items-center gap-3 p-3 rounded-lg transition-colors group relative ${location.pathname === '/notifications' ? 'bg-blue-600 text-white shadow-lg shadow-blue-100' : 'text-gray-700 hover:bg-blue-50 hover:text-blue-600'}`}>
                        <Bell size={20} className="group-hover:scale-110 transition-transform" />
                        <span className="font-medium">Notifications</span>
                        {unreadCount > 0 && (
                            <span className="absolute top-2 right-2 w-5 h-5 bg-red-500 text-white text-[10px] font-bold flex items-center justify-center rounded-full border-2 border-white">
                                {unreadCount}
                            </span>
                        )}
                    </Link>
                </nav>

                <div className="p-4 border-t border-gray-200">
                    <div className="flex items-center gap-3 mb-4 p-2">
                        <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center text-gray-600 font-bold uppercase">
                            {userName.charAt(0)}
                        </div>
                        <div className="flex flex-col overflow-hidden">
                            <span className="text-sm font-semibold truncate">{userName}</span>
                            <span className="text-xs text-gray-500">Member</span>
                        </div>
                    </div>
                    <button
                        onClick={handleLogout}
                        className="w-full flex items-center gap-3 p-3 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    >
                        <LogOut size={20} />
                        <span className="font-medium">Logout</span>
                    </button>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 flex flex-col overflow-hidden">
                <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-8">
                    <h2 className="text-xl font-semibold text-gray-800 uppercase tracking-wide">
                        {window.location.pathname === '/' ? 'Challenges' :
                            window.location.pathname.split('/').pop().replace('-', ' ')}
                    </h2>
                    <div className="flex items-center gap-6">
                        <div className="relative">
                            <input
                                type="text"
                                placeholder="Search..."
                                className="pl-10 pr-4 py-2 bg-gray-100 border-none rounded-full text-sm focus:ring-2 focus:ring-blue-500 w-64 lg:w-96"
                            />
                            <svg className="w-4 h-4 text-gray-400 absolute left-4 top-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                            </svg>
                        </div>
                    </div>
                </header>

                <section className="flex-1 overflow-y-auto p-8">
                    <Outlet />
                </section>
            </main>
        </div>
    );
};

export default MainLayout;
