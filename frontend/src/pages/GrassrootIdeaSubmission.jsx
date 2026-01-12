import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import { Send, AlertCircle, CheckCircle2, Info } from 'lucide-react';

const GrassrootIdeaSubmission = () => {
    const [categories, setCategories] = useState([]);
    const [subcategories, setSubcategories] = useState([]);
    const [formData, setFormData] = useState({
        improvement_category: '',
        improvement_sub_category: '',
        proposed_idea: '',
        business_value: '',
        monetary_value: '',
        non_monetary_value: '',
        assumptions: '',
        key_risks: '',
        additional_information: ''
    });
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState(false);
    const navigate = useNavigate();
    const userId = localStorage.getItem('iris_user_id');

    useEffect(() => {
        const fetchCategories = async () => {
            try {
                const response = await api.get('improvement-categories/');
                setCategories(response.data);
            } catch (error) {
                console.error("Error fetching categories:", error);
            }
        };
        fetchCategories();
    }, []);

    const handleCategoryChange = async (e) => {
        const categoryId = e.target.value;
        setFormData({ ...formData, improvement_category: categoryId, improvement_sub_category: '' });
        if (categoryId) {
            try {
                const response = await api.get(`improvement-subcategories/?category_id=${categoryId}`);
                setSubcategories(response.data);
            } catch (error) {
                console.error("Error fetching subcategories:", error);
            }
        } else {
            setSubcategories([]);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            await api.post('grassroot-ideas/', { ...formData, ideator: userId });
            setSuccess(true);
            setTimeout(() => navigate('/'), 3000);
        } catch (error) {
            console.error("Error submitting idea:", error);
            alert("Failed to submit idea. Please check the fields.");
        } finally {
            setLoading(false);
        }
    };

    if (success) {
        return (
            <div className="flex flex-col items-center justify-center h-full text-center space-y-6">
                <div className="w-20 h-20 bg-green-100 text-green-600 rounded-full flex items-center justify-center animate-bounce">
                    <CheckCircle2 size={48} />
                </div>
                <h2 className="text-3xl font-extrabold text-gray-900">Idea Submitted!</h2>
                <p className="text-gray-500 max-w-md">
                    Thank you for your valuable contribution. Your idea has been sent to your Reporting Manager for review.
                </p>
                <p className="text-blue-600 font-medium">Redirecting to dashboard...</p>
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto">
            <div className="mb-8 flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-extrabold text-gray-900">Submit Grassroot Idea</h2>
                    <p className="text-gray-500">Every big change starts with a small idea.</p>
                </div>
                <div className="bg-blue-50 text-blue-700 p-4 rounded-xl flex items-center gap-3 text-sm font-medium border border-blue-100 max-w-xs">
                    <Info size={24} className="shrink-0" />
                    <span>Your submission will be reviewed by your RM and IBU Head.</span>
                </div>
            </div>

            <form onSubmit={handleSubmit} className="bg-white rounded-3xl shadow-sm border border-gray-100 p-10 space-y-8">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <div className="space-y-2">
                        <label className="text-sm font-bold text-gray-700">Improvement Category</label>
                        <select
                            className="w-full p-4 bg-gray-50 border-2 border-gray-100 rounded-xl focus:bg-white focus:border-blue-500 outline-none transition-all"
                            value={formData.improvement_category}
                            onChange={handleCategoryChange}
                            required
                        >
                            <option value="">Select Category</option>
                            {categories.map(c => (
                                <option key={c.id} value={c.id}>{c.name}</option>
                            ))}
                        </select>
                    </div>
                    <div className="space-y-2">
                        <label className="text-sm font-bold text-gray-700">Sub-Category</label>
                        <select
                            className="w-full p-4 bg-gray-50 border-2 border-gray-100 rounded-xl focus:bg-white focus:border-blue-500 outline-none transition-all"
                            value={formData.improvement_sub_category}
                            onChange={(e) => setFormData({ ...formData, improvement_sub_category: e.target.value })}
                            required
                            disabled={!formData.improvement_category}
                        >
                            <option value="">Select Sub-Category</option>
                            {subcategories.map(s => (
                                <option key={s.id} value={s.id}>{s.name}</option>
                            ))}
                        </select>
                    </div>
                </div>

                <div className="space-y-2">
                    <label className="text-sm font-bold text-gray-700">Your Proposed Idea</label>
                    <textarea
                        rows="4"
                        className="w-full p-4 bg-gray-50 border-2 border-gray-100 rounded-xl focus:bg-white focus:border-blue-500 outline-none transition-all"
                        value={formData.proposed_idea}
                        onChange={(e) => setFormData({ ...formData, proposed_idea: e.target.value })}
                        placeholder="Describe your idea in detail..."
                        required
                    />
                </div>

                <div className="space-y-6">
                    <h4 className="text-lg font-bold text-gray-800 border-b pb-2">Business Value</h4>
                    <div className="grid grid-cols-1 gap-6">
                        <div className="space-y-2">
                            <label className="text-sm font-bold text-gray-700">Monetary Value (Optional)</label>
                            <textarea
                                className="w-full p-4 bg-gray-50 border-2 border-gray-100 rounded-xl focus:bg-white focus:border-blue-500 outline-none transition-all"
                                value={formData.monetary_value}
                                onChange={(e) => setFormData({ ...formData, monetary_value: e.target.value })}
                                placeholder="Expected cost savings or revenue generation..."
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-bold text-gray-700">Non-Monetary Value</label>
                            <textarea
                                className="w-full p-4 bg-gray-50 border-2 border-gray-100 rounded-xl focus:bg-white focus:border-blue-500 outline-none transition-all"
                                value={formData.non_monetary_value}
                                onChange={(e) => setFormData({ ...formData, non_monetary_value: e.target.value })}
                                placeholder="Efficiency gains, customer satisfaction, etc..."
                                required
                            />
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-6 border-t">
                    <div className="space-y-2">
                        <label className="text-sm font-bold text-gray-700 flex items-center gap-2">
                            <AlertCircle size={16} className="text-amber-500" /> Assumptions
                        </label>
                        <textarea
                            className="w-full p-4 bg-gray-50 border-2 border-gray-100 rounded-xl focus:bg-white focus:border-blue-500 outline-none transition-all"
                            value={formData.assumptions}
                            onChange={(e) => setFormData({ ...formData, assumptions: e.target.value })}
                            required
                        />
                    </div>
                    <div className="space-y-2">
                        <label className="text-sm font-bold text-gray-700 flex items-center gap-2">
                            <AlertCircle size={16} className="text-red-500" /> Key Risks
                        </label>
                        <textarea
                            className="w-full p-4 bg-gray-50 border-2 border-gray-100 rounded-xl focus:bg-white focus:border-blue-500 outline-none transition-all"
                            value={formData.key_risks}
                            onChange={(e) => setFormData({ ...formData, key_risks: e.target.value })}
                            required
                        />
                    </div>
                </div>

                <div className="flex justify-end gap-4 pt-8">
                    <button
                        type="button"
                        onClick={() => navigate('/')}
                        className="px-8 py-3 rounded-xl font-bold text-gray-500 hover:bg-gray-100 transition-all"
                    >
                        Cancel
                    </button>
                    <button
                        type="submit"
                        disabled={loading}
                        className="bg-blue-600 text-white px-10 py-3 rounded-xl font-bold shadow-lg shadow-blue-100 hover:bg-blue-700 hover:scale-105 active:scale-95 transition-all flex items-center gap-2 disabled:opacity-50"
                    >
                        <Send size={20} />
                        {loading ? 'Submitting...' : 'Submit Idea'}
                    </button>
                </div>
            </form>
        </div>
    );
};

export default GrassrootIdeaSubmission;
