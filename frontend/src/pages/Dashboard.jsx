import React, { useState, useEffect } from 'react';
import api from '../api';
import { Target, Calendar, Users, Briefcase } from 'lucide-react';

const Dashboard = () => {
    const [challenges, setChallenges] = useState([]);
    const [stats, setStats] = useState({ member_count: 0, idea_count: 0, challenge_count: 0 });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [challengesRes, statsRes] = await Promise.all([
                    api.get('challenges/?filter=active'),
                    api.get('stats/')
                ]);
                setChallenges(challengesRes.data);
                setStats(statsRes.data);
            } catch (error) {
                console.error("Error fetching dashboard data:", error);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    if (loading) {
        return <div className="flex items-center justify-center h-full text-blue-600 font-bold">Loading Dashboard...</div>;
    }

    return (
        <div className="space-y-8">
            {/* Stats Section */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <StatCard
                    icon={<Users className="text-blue-600" />}
                    title="Community Members"
                    value={stats.member_count}
                    color="bg-blue-100"
                />
                <StatCard
                    icon={<Briefcase className="text-green-600" />}
                    title="Ideas Submitted"
                    value={stats.idea_count}
                    color="bg-green-100"
                />
                <StatCard
                    icon={<Target className="text-purple-600" />}
                    title="Live Challenges"
                    value={stats.challenge_count}
                    color="bg-purple-100"
                />
            </div>

            {/* Featured Header */}
            <div className="bg-gradient-to-r from-blue-600 to-indigo-700 rounded-2xl p-8 text-white shadow-xl relative overflow-hidden">
                <div className="relative z-10">
                    <h1 className="text-3xl font-extrabold mb-4">Innovate for Tomorrow</h1>
                    <p className="text-blue-100 max-w-2xl mb-6 text-lg">
                        Join our community of visionaries. Submit your ideas, solve challenges, and shape the future of Grassroot Innovation.
                    </p>
                    <button className="bg-white text-blue-600 px-8 py-3 rounded-full font-bold hover:shadow-lg hover:scale-105 transition-all">
                        See All Challenges
                    </button>
                </div>
                <div className="absolute top-0 right-0 p-8 opacity-20">
                    <Target size={180} />
                </div>
            </div>

            {/* Challenges Grid */}
            <div>
                <div className="flex items-center justify-between mb-6">
                    <h3 className="text-2xl font-bold text-gray-800">Live Challenges</h3>
                    <div className="bg-white px-4 py-2 rounded-lg border border-gray-200 text-sm font-medium text-gray-500">
                        Sort by: Newest
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {challenges.map(challenge => (
                        <ChallengeCard key={challenge.challenge_id} challenge={challenge} />
                    ))}
                    {challenges.length === 0 && (
                        <div className="col-span-full py-12 text-center text-gray-500 bg-white rounded-xl border-2 border-dashed border-gray-200">
                            No live challenges at the moment. Check back soon!
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

const StatCard = ({ icon, title, value, color }) => (
    <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex items-center gap-6 hover:shadow-md transition-shadow">
        <div className={`p-4 rounded-xl ${color}`}>
            {icon}
        </div>
        <div className="flex flex-col">
            <span className="text-gray-500 text-sm font-medium uppercase tracking-wider">{title}</span>
            <span className="text-3xl font-bold">{value}</span>
        </div>
    </div>
);

const ChallengeCard = ({ challenge }) => (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-xl hover:-translate-y-1 transition-all flex flex-col group">
        <div className="h-48 bg-gray-200 relative overflow-hidden">
            {challenge.challenge_icon ? (
                <img
                    src={challenge.challenge_icon}
                    alt={challenge.title}
                    className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                />
            ) : (
                <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200">
                    <Target size={48} className="text-gray-300" />
                </div>
            )}
            <div className="absolute top-4 right-4 bg-white/90 backdrop-blur-sm px-3 py-1 rounded-full text-xs font-bold text-blue-600 shadow-sm">
                {challenge.visibility}
            </div>
        </div>
        <div className="p-6 flex-1 flex flex-col">
            <h4 className="text-xl font-bold mb-3 line-clamp-2 min-h-[3.5rem]">{challenge.title}</h4>
            <p className="text-gray-600 text-sm line-clamp-3 mb-6 flex-1">
                {challenge.description}
            </p>
            <div className="flex items-center justify-between text-sm text-gray-500 pt-4 border-t border-gray-50">
                <div className="flex items-center gap-2 font-medium">
                    <Calendar size={16} />
                    <span>Ends {new Date(challenge.end_date).toLocaleDateString()}</span>
                </div>
                <button className="text-blue-600 font-bold hover:underline">
                    Join Now
                </button>
            </div>
        </div>
    </div>
);

export default Dashboard;
