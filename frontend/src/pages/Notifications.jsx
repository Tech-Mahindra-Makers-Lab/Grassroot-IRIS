import React, { useState, useEffect } from 'react';
import api from '../api';
import { Bell, CheckCircle, Clock, ExternalLink } from 'lucide-react';

const Notifications = () => {
    const [notifications, setNotifications] = useState([]);
    const [loading, setLoading] = useState(true);
    const userId = localStorage.getItem('iris_user_id');

    useEffect(() => {
        const fetchNotifications = async () => {
            try {
                const response = await api.get(`notifications/?user_id=${userId}`);
                setNotifications(response.data);
            } catch (error) {
                console.error("Error fetching notifications:", error);
            } finally {
                setLoading(false);
            }
        };
        if (userId) fetchNotifications();
    }, [userId]);

    const markAsRead = async (id) => {
        try {
            await api.post(`notifications/${id}/mark_as_read/`);
            setNotifications(notifications.map(n =>
                n.notification_id === id ? { ...n, is_read: true } : n
            ));
        } catch (error) {
            console.error("Error marking notification as read:", error);
        }
    };

    if (loading) return <div className="text-blue-600 font-bold">Loading...</div>;

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <div className="flex items-center justify-between">
                <h3 className="text-2xl font-bold text-gray-800">Your Notifications</h3>
                <span className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-xs font-bold uppercase">
                    {notifications.filter(n => !n.is_read).length} Unread
                </span>
            </div>

            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                {notifications.map((n, index) => (
                    <div
                        key={n.notification_id}
                        className={`p-6 flex items-start gap-6 border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors ${!n.is_read ? 'bg-blue-50/30' : ''}`}
                    >
                        <div className={`p-3 rounded-xl ${!n.is_read ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-400'}`}>
                            <Bell size={20} />
                        </div>
                        <div className="flex-1">
                            <div className="flex items-center justify-between mb-1">
                                <span className={`font-bold ${!n.is_read ? 'text-gray-900' : 'text-gray-500'}`}>
                                    {n.message}
                                </span>
                                <span className="text-xs text-gray-400 flex items-center gap-1">
                                    <Clock size={12} />
                                    {new Date(n.created_at).toLocaleString()}
                                </span>
                            </div>
                            <div className="flex items-center gap-4 mt-4">
                                {n.link && (
                                    <a
                                        href={n.link}
                                        className="text-blue-600 text-sm font-bold flex items-center gap-1 hover:underline underline-offset-4"
                                    >
                                        View Details <ExternalLink size={14} />
                                    </a>
                                )}
                                {!n.is_read && (
                                    <button
                                        onClick={() => markAsRead(n.notification_id)}
                                        className="text-gray-400 text-sm font-medium hover:text-blue-600 flex items-center gap-1"
                                    >
                                        <CheckCircle size={14} /> Mark as Read
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>
                ))}
                {notifications.length === 0 && (
                    <div className="p-12 text-center text-gray-500 italic">
                        You don't have any notifications yet.
                    </div>
                )}
            </div>
        </div>
    );
};

export default Notifications;
