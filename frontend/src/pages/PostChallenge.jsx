import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import { Plus, Trash2, UserPlus, Target, Calendar, ClipboardCheck, ArrowLeft, ArrowRight, Save } from 'lucide-react';

const PostChallenge = () => {
    const [step, setStep] = useState(1);
    const [loading, setLoading] = useState(false);
    const [params, setParams] = useState([]);
    const navigate = useNavigate();
    const userId = localStorage.getItem('iris_user_id');

    // Step 1: Basic Info
    const [challengeData, setChallengeData] = useState({
        title: '',
        description: '',
        start_date: '',
        end_date: '',
        round1_eval_start: '',
        round1_eval_end: '',
        round2_eval_start: '',
        round2_eval_end: '',
        keywords: '',
        visibility: 'PUBLIC',
        target_audience: 'INTERNAL',
        expected_outcome: '',
        key_insights: '',
    });

    // Step 2: Panels
    const [panels, setPanels] = useState([]);

    // Step 3: Mentors (Assigned to Panels)
    const [mentors, setMentors] = useState([]); // Array of { panelIndex, email, name }

    const [challengeId, setChallengeId] = useState(null);

    useEffect(() => {
        const fetchParams = async () => {
            try {
                const response = await api.get('review-parameters/');
                setParams(response.data);
            } catch (err) {
                console.error("Error fetching params:", err);
            }
        };
        fetchParams();
    }, []);

    const handleNext = async () => {
        if (step === 1) {
            setLoading(true);
            try {
                const res = await api.post('challenges/', { ...challengeData, created_by: userId });
                setChallengeId(res.data.challenge_id);
                setStep(2);
            } catch (err) {
                alert("Error saving challenge details. Check dates and fields.");
            } finally {
                setLoading(false);
            }
        } else if (step === 2) {
            setStep(3);
        }
    };

    const handleAddPanel = () => {
        const roundNum = panels.filter(p => p.round === 1).length < 3 ? 1 : 2;
        if (roundNum === 2 && panels.filter(p => p.round === 2).length >= 2) {
            alert("Max panels reached (3 for R1, 2 for R2)");
            return;
        }
        setPanels([...panels, { panel_name: '', description: '', round: roundNum }]);
    };

    const handlePanelChange = (index, field, value) => {
        const newPanels = [...panels];
        newPanels[index][field] = value;
        setPanels(newPanels);
    };

    const savePanels = async () => {
        setLoading(true);
        try {
            for (const panel of panels) {
                await api.post('challenge-panels/', { ...panel, challenge: challengeId, round_number: panel.round });
            }
            // Re-fetch panels from API to get their real IDs for Step 3
            const res = await api.get(`challenge-panels/?challenge_id=${challengeId}`);
            setPanels(res.data.map(p => ({ ...p, round: p.round_number })));
            setStep(3);
        } catch (err) {
            alert("Error saving panels.");
        } finally {
            setLoading(false);
        }
    };

    const [mentorEmail, setMentorEmail] = useState('');
    const [selectedPanelId, setSelectedPanelId] = useState('');

    const handleAddMentor = async () => {
        if (!mentorEmail || !selectedPanelId) return;
        setLoading(true);
        try {
            // Find user by email (using our search API or broad list)
            const userRes = await api.get(`users/?email=${mentorEmail}`);
            if (userRes.data.length === 0) {
                alert("User not found.");
                return;
            }
            const mentorUser = userRes.data[0];
            await api.post('challenge-mentors/', { panel: selectedPanelId, mentor: mentorUser.user_id });
            // Re-fetch mentors if needed or just add to local state
            alert(`Mentor ${mentorUser.full_name} added.`);
            setMentorEmail('');
        } catch (err) {
            alert("Error adding mentor.");
        } finally {
            setLoading(false);
        }
    };

    const finalizeChallenge = async () => {
        try {
            await api.patch(`challenges/${challengeId}/`, { status: 'LIVE' });
            alert("Challenge is now LIVE!");
            navigate('/');
        } catch (err) {
            alert("Error finalizing challenge.");
        }
    };

    return (
        <div className="max-w-5xl mx-auto pb-20">
            {/* Stepper */}
            <div className="flex items-center justify-between mb-12 bg-white p-6 rounded-3xl shadow-sm border border-gray-100">
                <StepIndicator num={1} title="Details" active={step === 1} completed={step > 1} />
                <div className="flex-1 h-1 bg-gray-100 mx-4 rounded-full overflow-hidden">
                    <div className={`h-full bg-blue-600 transition-all duration-500 ${step > 1 ? 'w-full' : 'w-0'}`}></div>
                </div>
                <StepIndicator num={2} title="Panels" active={step === 2} completed={step > 2} />
                <div className="flex-1 h-1 bg-gray-100 mx-4 rounded-full overflow-hidden">
                    <div className={`h-full bg-blue-600 transition-all duration-500 ${step > 2 ? 'w-full' : 'w-0'}`}></div>
                </div>
                <StepIndicator num={3} title="Mentors" active={step === 3} completed={step > 3} />
            </div>

            {step === 1 && (
                <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                    <Section title="Basic Information" icon={<Target className="text-blue-600" />}>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                            <Input label="Challenge Title" placeholder="e.g. Green Energy Solutions 2026"
                                value={challengeData.title} onChange={v => setChallengeData({ ...challengeData, title: v })} />
                            <Input label="Keywords (Comma separated)" placeholder="solar, wind, sustainability"
                                value={challengeData.keywords} onChange={v => setChallengeData({ ...challengeData, keywords: v })} />
                            <div className="md:col-span-2">
                                <label className="text-sm font-bold text-gray-700 block mb-2">Detailed Description</label>
                                <textarea className="w-full p-4 bg-gray-50 border-2 border-gray-100 rounded-xl focus:border-blue-500 outline-none transition-all h-32"
                                    value={challengeData.description} onChange={e => setChallengeData({ ...challengeData, description: e.target.value })} />
                            </div>
                        </div>
                    </Section>

                    <Section title="Important Dates" icon={<Calendar className="text-green-600" />}>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                            <DateInput label="Start Date" value={challengeData.start_date} onChange={v => setChallengeData({ ...challengeData, start_date: v })} />
                            <DateInput label="End Date" value={challengeData.end_date} onChange={v => setChallengeData({ ...challengeData, end_date: v })} />
                            <DateInput label="R1 Eval Start" value={challengeData.round1_eval_start} onChange={v => setChallengeData({ ...challengeData, round1_eval_start: v })} />
                            <DateInput label="R1 Eval End" value={challengeData.round1_eval_end} onChange={v => setChallengeData({ ...challengeData, round1_eval_end: v })} />
                        </div>
                    </Section>

                    <div className="flex justify-end gap-4">
                        <button className="px-8 py-3 rounded-xl font-bold text-gray-500 hover:bg-white transition-all flex items-center gap-2" onClick={() => navigate('/')}>
                            <ArrowLeft size={20} /> Cancel
                        </button>
                        <button className="bg-blue-600 text-white px-10 py-3 rounded-xl font-bold shadow-lg shadow-blue-100 hover:bg-blue-700 hover:scale-105 transition-all flex items-center gap-2"
                            onClick={handleNext} disabled={loading}>
                            {loading ? 'Saving...' : 'Set Panels'} <ArrowRight size={20} />
                        </button>
                    </div>
                </div>
            )}

            {step === 2 && (
                <div className="space-y-8 animate-in fade-in slide-in-from-right-4 duration-500">
                    <div className="flex items-center justify-between">
                        <h3 className="text-2xl font-extrabold text-gray-900">Define Review Panels</h3>
                        <button className="bg-blue-50 text-blue-600 px-6 py-2 rounded-xl font-bold flex items-center gap-2 hover:bg-blue-100 transition-all"
                            onClick={handleAddPanel}>
                            <Plus size={20} /> Add Panel
                        </button>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {panels.map((p, idx) => (
                            <div key={idx} className="bg-white p-6 rounded-3xl border border-gray-100 shadow-sm space-y-4 group">
                                <div className="flex items-center justify-between">
                                    <span className={`px-3 py-1 rounded-full text-xs font-bold ${p.round === 1 ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'}`}>
                                        Round {p.round}
                                    </span>
                                    <button className="text-gray-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                                        onClick={() => setPanels(panels.filter((_, i) => i !== idx))}>
                                        <Trash2 size={18} />
                                    </button>
                                </div>
                                <input className="text-xl font-bold w-full focus:outline-none border-b border-transparent focus:border-blue-200"
                                    placeholder="Panel Name" value={p.panel_name} onChange={e => handlePanelChange(idx, 'panel_name', e.target.value)} />
                                <textarea className="text-sm text-gray-500 w-full focus:outline-none h-20 bg-gray-50 p-3 rounded-xl"
                                    placeholder="What will this panel evaluate?" value={p.description} onChange={e => handlePanelChange(idx, 'description', e.target.value)} />
                            </div>
                        ))}
                    </div>

                    <div className="flex justify-end gap-4 mt-12">
                        <button className="bg-blue-600 text-white px-10 py-3 rounded-xl font-bold shadow-lg shadow-blue-100 hover:bg-blue-700 hover:scale-105 transition-all flex items-center gap-2"
                            onClick={savePanels} disabled={loading}>
                            {loading ? 'Saving...' : 'Assign Mentors'} <ArrowRight size={20} />
                        </button>
                    </div>
                </div>
            )}

            {step === 3 && (
                <div className="space-y-8 animate-in fade-in slide-in-from-right-4 duration-500">
                    <Section title="Assign Mentors to Panels" icon={<UserPlus className="text-purple-600" />}>
                        <div className="flex flex-wrap gap-4 items-end mb-8 bg-gray-50 p-6 rounded-2xl">
                            <div className="flex-1 min-w-[250px] space-y-2">
                                <label className="text-xs font-bold text-gray-500 uppercase">Mentor Email</label>
                                <input className="w-full p-3 border-2 border-gray-100 rounded-xl focus:border-blue-500 outline-none"
                                    value={mentorEmail} onChange={e => setMentorEmail(e.target.value)} placeholder="colleague@example.com" />
                            </div>
                            <div className="flex-1 min-w-[200px] space-y-2">
                                <label className="text-xs font-bold text-gray-500 uppercase">Target Panel</label>
                                <select className="w-full p-3 border-2 border-gray-100 rounded-xl outline-none"
                                    value={selectedPanelId} onChange={e => setSelectedPanelId(e.target.value)}>
                                    <option value="">Select a Panel</option>
                                    {panels.map(p => (
                                        <option key={p.panel_id} value={p.panel_id}>{p.panel_name} (R{p.round})</option>
                                    ))}
                                </select>
                            </div>
                            <button className="bg-indigo-600 text-white px-8 py-3 rounded-xl font-bold flex items-center gap-2 hover:bg-indigo-700 transition-all"
                                onClick={handleAddMentor} disabled={loading}>
                                <Plus size={18} /> Add
                            </button>
                        </div>
                    </Section>

                    <div className="flex justify-center pt-12">
                        <button className="bg-green-600 text-white px-12 py-4 rounded-2xl font-bold shadow-xl shadow-green-100 hover:bg-green-700 hover:scale-105 active:scale-95 transition-all flex items-center gap-3 text-lg"
                            onClick={finalizeChallenge}>
                            <ClipboardCheck size={24} /> Finalize & Make Live
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

const StepIndicator = ({ num, title, active, completed }) => (
    <div className="flex items-center gap-3">
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center font-bold text-sm transition-all shadow-sm ${completed ? 'bg-green-100 text-green-600' : active ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-400'
            }`}>
            {completed ? <ClipboardCheck size={20} /> : num}
        </div>
        <span className={`font-bold transition-colors ${active || completed ? 'text-gray-900' : 'text-gray-400'}`}>{title}</span>
    </div>
);

const Section = ({ title, icon, children }) => (
    <div className="bg-white p-10 rounded-3xl shadow-sm border border-gray-100">
        <div className="flex items-center gap-3 mb-8">
            <div className="p-2 bg-gray-50 rounded-lg">{icon}</div>
            <h3 className="text-xl font-extrabold text-gray-900">{title}</h3>
        </div>
        {children}
    </div>
);

const Input = ({ label, placeholder, value, onChange }) => (
    <div className="space-y-2">
        <label className="text-sm font-bold text-gray-700">{label}</label>
        <input className="w-full p-4 bg-gray-50 border-2 border-gray-100 rounded-xl focus:bg-white focus:border-blue-500 outline-none transition-all placeholder:text-gray-400"
            placeholder={placeholder} value={value} onChange={e => onChange(e.target.value)} />
    </div>
);

const DateInput = ({ label, value, onChange }) => (
    <div className="space-y-1">
        <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">{label}</label>
        <input type="date" className="w-full p-3 bg-gray-50 border-2 border-gray-100 rounded-xl focus:border-blue-500 outline-none text-sm"
            value={value} onChange={e => onChange(e.target.value)} />
    </div>
);

export default PostChallenge;
