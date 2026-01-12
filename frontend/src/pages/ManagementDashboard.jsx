import React, { useState, useEffect } from 'react';
import api from '../api';
import { CheckCircle2, XCircle, RefreshCw, FileText, User, Filter, AlertCircle } from 'lucide-react';

const ManagementDashboard = () => {
    const [activeTab, setActiveTab] = useState('RM'); // OR 'IBU'
    const [ideas, setIdeas] = useState([]);
    const [loading, setLoading] = useState(true);
    const userId = localStorage.getItem('iris_user_id');

    useEffect(() => {
        const fetchIdeas = async () => {
            setLoading(true);
            try {
                const endpoint = activeTab === 'RM'
                    ? `grassroot-ideas/?status=SUBMITTED_RM` // RM sees ideas submitted to them
                    : `grassroot-ideas/?status=APPROVED_RM`; // IBU sees ideas approved by RM

                const response = await api.get(endpoint);
                setIdeas(response.data);
            } catch (err) {
                console.error("Error fetching management ideas:", err);
            } finally {
                setLoading(false);
            }
        };
        fetchIdeas();
    }, [activeTab]);

    const handleEvaluation = async (ideaId, action) => {
        // action: 'APPROVE', 'REJECT', 'REWORK'
        try {
            let nextStatus = '';
            if (activeTab === 'RM') {
                if (action === 'APPROVE') nextStatus = 'APPROVED_RM';
                else if (action === 'REJECT') nextStatus = 'REJECTED_RM';
                else if (action === 'REWORK') nextStatus = 'REWORK_RM';
            } else {
                if (action === 'APPROVE') nextStatus = 'APPROVED_IBU';
                else if (action === 'REJECT') nextStatus = 'REJECTED_IBU';
                else if (action === 'REWORK') nextStatus = 'REWORK_IBU';
            }

            await api.patch(`grassroot-ideas/${ideaId}/`, { status: nextStatus });
            setIdeas(ideas.filter(i => i.idea_id !== ideaId));
            alert(`Idea ${action.toLowerCase()}d successfully.`);
        } catch (err) {
            alert("Error processing evaluation.");
        }
    };

    return (
        <div className="space-y-8 max-w-6xl mx-auto">
            <div className="flex items-center justify-between bg-white p-2 rounded-2xl shadow-sm border border-gray-100">
                <div className="flex gap-2">
                    <TabButton active={activeTab === 'RM'} onClick={() => setActiveTab('RM')}>Manager Review (RM)</TabButton>
                    <TabButton active={activeTab === 'IBU'} onClick={() => setActiveTab('IBU')}>Head Review (IBU)</TabButton>
                </div>
                <div className="px-4 py-2 text-sm text-gray-500 font-medium">
                    Pending Actions: <span className="text-blue-600 font-bold">{ideas.length}</span>
                </div>
            </div>

            {loading ? (
                <div className="flex items-center justify-center p-20 text-blue-600 font-bold">Loading pending reviews...</div>
            ) : (
                <div className="grid grid-cols-1 gap-6">
                    {ideas.map(idea => (
                        <div key={idea.idea_id} className="bg-white rounded-3xl shadow-sm border border-gray-100 overflow-hidden flex flex-col md:flex-row group transition-all hover:shadow-xl">
                            <div className="p-8 flex-1 space-y-4">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2 text-sm text-gray-400 font-medium">
                                        <User size={14} />
                                        <span>{idea.ideator_name}</span>
                                        <span className="mx-2">•</span>
                                        <FileText size={14} />
                                        <span>{idea.category_name}</span>
                                    </div>
                                    <span className="bg-amber-100 text-amber-700 px-3 py-1 rounded-full text-xs font-bold uppercase">
                                        Pending {activeTab}
                                    </span>
                                </div>

                                <h4 className="text-xl font-bold text-gray-900 leading-tight">
                                    {idea.proposed_idea.substring(0, 150)}...
                                </h4>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-gray-50 p-4 rounded-xl text-sm">
                                    <div>
                                        <span className="font-bold text-gray-700 block mb-1">Business Value</span>
                                        <p className="text-gray-500 line-clamp-2">{idea.business_value}</p>
                                    </div>
                                    <div>
                                        <span className="font-bold text-gray-700 block mb-1">Key Risks</span>
                                        <p className="text-gray-500 line-clamp-2">{idea.key_risks}</p>
                                    </div>
                                </div>
                            </div>

                            <div className="bg-gray-50/50 p-8 flex flex-col justify-center gap-3 border-t md:border-t-0 md:border-l border-gray-100 min-w-[200px]">
                                <button
                                    onClick={() => handleEvaluation(idea.idea_id, 'APPROVE')}
                                    className="w-full bg-green-600 text-white py-3 rounded-xl font-bold flex items-center justify-center gap-2 hover:bg-green-700 hover:scale-105 transition-all shadow-md shadow-green-100"
                                >
                                    <CheckCircle2 size={18} /> Approve
                                </button>
                                <button
                                    onClick={() => handleEvaluation(idea.idea_id, 'REWORK')}
                                    className="w-full bg-amber-500 text-white py-3 rounded-xl font-bold flex items-center justify-center gap-2 hover:bg-amber-600 hover:scale-105 transition-all shadow-md shadow-amber-100"
                                >
                                    <RefreshCw size={18} /> Rework
                                </button>
                                <button
                                    onClick={() => handleEvaluation(idea.idea_id, 'REJECT')}
                                    className="w-full bg-red-100 text-red-600 py-3 rounded-xl font-bold flex items-center justify-center gap-2 hover:bg-red-200 transition-all"
                                >
                                    <XCircle size={18} /> Reject
                                </button>
                            </div>
                        </div>
                    ))}

                    {ideas.length === 0 && (
                        <div className="text-center py-20 bg-white rounded-3xl border-2 border-dashed border-gray-100">
                            <div className="inline-flex items-center justify-center w-16 h-16 bg-gray-50 rounded-full text-gray-300 mb-4">
                                <CheckCircle2 size={32} />
                            </div>
                            <h5 className="text-lg font-bold text-gray-400 uppercase tracking-widest">All Caught Up!</h5>
                            <p className="text-gray-400">No pending ideas to review for {activeTab}.</p>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

const TabButton = ({ active, children, onClick }) => (
    <button
        onClick={onClick}
        className={`px-8 py-3 rounded-xl font-bold transition-all ${active ? 'bg-blue-600 text-white shadow-lg shadow-blue-100' : 'text-gray-500 hover:bg-gray-50'
            }`}
    >
        {children}
    </button>
);

export default ManagementDashboard;
