import { useState, useEffect } from 'react';
import axios from 'axios';
import { API, useAuth } from '@/App';
import { Bot, Plus, Edit2, Trash2, X, Save, Lock, Shield } from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { toast } from 'sonner';

const categoryColors = {
    'Sovereign Oversight': 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    'Executive & Architecture': 'bg-purple-500/20 text-purple-400 border-purple-500/30',
    'Creative Engine': 'bg-pink-500/20 text-pink-400 border-pink-500/30',
    'Systems & Ops': 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    'Growth & Commercial': 'bg-green-500/20 text-green-400 border-green-500/30',
    'Data & Integrity': 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
    'Legacy & Integrity': 'bg-orange-500/20 text-orange-400 border-orange-500/30',
    'Core Resolution': 'bg-red-500/20 text-red-400 border-red-500/30',
    'Business & Risk': 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    'Creative & Brand': 'bg-violet-500/20 text-violet-400 border-violet-500/30',
    'Governance & IP': 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    'Quality & Trust': 'bg-teal-500/20 text-teal-400 border-teal-500/30',
    'Reserved Expansion': 'bg-gray-500/20 text-gray-400 border-gray-500/30',
};

const OperatorCard = ({ operator, onEdit, onDelete, canEdit, isSovereign }) => {
    const isCanonical = operator.is_canonical;
    const canModify = canEdit && (!isCanonical || isSovereign);
    
    return (
        <div className={`bg-card border p-6 transition-colors ${isCanonical ? 'border-yellow-500/50' : 'border-border hover:border-primary/50'}`} data-testid={`operator-${operator.operator_id}`}>
            <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 border flex items-center justify-center ${isCanonical ? 'border-yellow-500 bg-yellow-500/10' : 'border-primary'}`}>
                        {isCanonical ? <Shield size={18} className="text-yellow-500" /> : <Bot size={18} className="text-primary" />}
                    </div>
                    <div>
                        <div className="font-mono text-xs text-muted-foreground">{operator.tai_d}</div>
                        <div className="font-mono text-sm font-bold uppercase">{operator.name}</div>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    {isCanonical && (
                        <span className="px-2 py-1 bg-yellow-500/20 text-yellow-400 font-mono text-[10px] border border-yellow-500/30 flex items-center gap-1">
                            <Lock size={10} /> CANONICAL
                        </span>
                    )}
                    {canModify && (
                        <div className="flex gap-1">
                            <button onClick={() => onEdit(operator)} className="p-2 hover:bg-secondary" data-testid={`edit-operator-${operator.operator_id}`}>
                                <Edit2 size={14} />
                            </button>
                            <button onClick={() => onDelete(operator)} className="p-2 hover:bg-destructive/20 text-destructive" data-testid={`delete-operator-${operator.operator_id}`}>
                                <Trash2 size={14} />
                            </button>
                        </div>
                    )}
                </div>
            </div>
            <p className="text-sm text-muted-foreground mb-4">{operator.capabilities} — {operator.role}</p>
            <div className="flex flex-wrap gap-2">
                <span className={`px-2 py-1 font-mono text-[10px] border ${categoryColors[operator.category] || 'bg-gray-500/20 text-gray-400 border-gray-500/30'}`}>
                    {operator.category}
                </span>
                <span className={`px-2 py-1 font-mono text-[10px] border ${operator.status === 'LOCKED' ? 'bg-green-500/20 text-green-400 border-green-500/30' : 'bg-gray-500/20 text-gray-400 border-gray-500/30'}`}>
                    {operator.status}
                </span>
                {operator.decision_weight && (
                    <span className="px-2 py-1 font-mono text-[10px] bg-primary/20 text-primary border border-primary/30">
                        WEIGHT: {operator.decision_weight}
                    </span>
                )}
            </div>
            <div className="mt-3 pt-3 border-t border-border">
                <span className="font-mono text-[10px] text-muted-foreground">AUTHORITY: {operator.authority}</span>
            </div>
        </div>
    );
};

const OperatorForm = ({ operator, onSave, onCancel }) => {
    const [form, setForm] = useState(operator || {
        tai_d: '', name: '', capabilities: '', role: '', authority: '', status: 'ACTIVE', category: 'Custom'
    });

    const handleSubmit = (e) => {
        e.preventDefault();
        onSave(form);
    };

    return (
        <form onSubmit={handleSubmit} className="bg-card border border-border p-6 space-y-4">
            <div className="flex justify-between items-center mb-4">
                <h3 className="font-mono text-lg font-bold uppercase">{operator ? 'EDIT OPERATOR' : 'NEW OPERATOR'}</h3>
                <button type="button" onClick={onCancel} className="p-2 hover:bg-secondary"><X size={18} /></button>
            </div>
            {!operator && (
                <div className="bg-blue-500/10 border border-blue-500/30 p-3 text-sm text-blue-400">
                    <strong>Note:</strong> New operators you create will NOT be canonical. They cannot outweigh or override canonical operators set by the sovereign.
                </div>
            )}
            <div className="grid grid-cols-2 gap-4">
                <div>
                    <label className="font-mono text-xs text-muted-foreground block mb-2">TAI-D IDENTIFIER *</label>
                    <input value={form.tai_d} onChange={(e) => setForm({...form, tai_d: e.target.value})} className="w-full bg-background border border-border px-3 py-2 font-mono text-sm" placeholder="USER-XXX" required disabled={!!operator} />
                </div>
                <div>
                    <label className="font-mono text-xs text-muted-foreground block mb-2">NAME *</label>
                    <input value={form.name} onChange={(e) => setForm({...form, name: e.target.value})} className="w-full bg-background border border-border px-3 py-2 font-mono text-sm" required />
                </div>
            </div>
            <div>
                <label className="font-mono text-xs text-muted-foreground block mb-2">CAPABILITIES *</label>
                <input value={form.capabilities} onChange={(e) => setForm({...form, capabilities: e.target.value})} className="w-full bg-background border border-border px-3 py-2 font-mono text-sm" required />
            </div>
            <div>
                <label className="font-mono text-xs text-muted-foreground block mb-2">ROLE *</label>
                <textarea value={form.role} onChange={(e) => setForm({...form, role: e.target.value})} className="w-full bg-background border border-border px-3 py-2 font-mono text-sm h-16" required />
            </div>
            <div className="grid grid-cols-2 gap-4">
                <div>
                    <label className="font-mono text-xs text-muted-foreground block mb-2">AUTHORITY *</label>
                    <input value={form.authority} onChange={(e) => setForm({...form, authority: e.target.value})} className="w-full bg-background border border-border px-3 py-2 font-mono text-sm" required />
                </div>
                <div>
                    <label className="font-mono text-xs text-muted-foreground block mb-2">STATUS</label>
                    <select value={form.status} onChange={(e) => setForm({...form, status: e.target.value})} className="w-full bg-background border border-border px-3 py-2 font-mono text-sm">
                        <option value="ACTIVE">ACTIVE</option>
                        <option value="INACTIVE">INACTIVE</option>
                    </select>
                </div>
            </div>
            <div>
                <label className="font-mono text-xs text-muted-foreground block mb-2">CATEGORY</label>
                <select value={form.category} onChange={(e) => setForm({...form, category: e.target.value})} className="w-full bg-background border border-border px-3 py-2 font-mono text-sm">
                    <option value="Custom">Custom</option>
                    <option value="Executive & Architecture">Executive & Architecture</option>
                    <option value="Creative Engine">Creative Engine</option>
                    <option value="Systems & Ops">Systems & Ops</option>
                    <option value="Growth & Commercial">Growth & Commercial</option>
                    <option value="Data & Integrity">Data & Integrity</option>
                    <option value="Quality & Trust">Quality & Trust</option>
                </select>
            </div>
            <button type="submit" className="w-full bg-primary text-primary-foreground p-3 font-mono text-sm tracking-wider uppercase flex items-center justify-center gap-2">
                <Save size={16} /> SAVE OPERATOR
            </button>
        </form>
    );
};

const PigPen = () => {
    const { user, canEdit } = useAuth();
    const [operators, setOperators] = useState([]);
    const [stats, setStats] = useState({ canonical_count: 0, user_count: 0 });
    const [loading, setLoading] = useState(true);
    const [showForm, setShowForm] = useState(false);
    const [editingOperator, setEditingOperator] = useState(null);
    const [selectedCategory, setSelectedCategory] = useState('all');
    const [categories, setCategories] = useState([]);

    // Check if current user is sovereign
    const isSovereign = user?.email === 'jonpearlandpig@gmail.com';

    useEffect(() => { fetchOperators(); }, [selectedCategory]);

    const fetchOperators = async () => {
        try {
            const params = selectedCategory !== 'all' ? `?category=${selectedCategory}` : '';
            const [opsRes, catsRes] = await Promise.all([
                axios.get(`${API}/pigpen${params}`),
                axios.get(`${API}/pigpen/categories/list`)
            ]);
            setOperators(opsRes.data.operators);
            setStats({
                canonical_count: opsRes.data.canonical_count || 0,
                user_count: opsRes.data.user_count || 0
            });
            setCategories(catsRes.data.categories || []);
        } catch (error) {
            console.error('Error:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async (form) => {
        try {
            if (editingOperator) {
                await axios.put(`${API}/pigpen/${editingOperator.operator_id}`, form, { withCredentials: true });
                toast.success('Operator updated');
            } else {
                await axios.post(`${API}/pigpen`, form, { withCredentials: true });
                toast.success('Operator created');
            }
            setShowForm(false);
            setEditingOperator(null);
            fetchOperators();
        } catch (error) {
            toast.error(error.response?.data?.detail || 'Error saving operator');
        }
    };

    const handleDelete = async (operator) => {
        if (operator.is_canonical && !isSovereign) {
            toast.error('Cannot delete canonical operator. Only sovereign authority can modify canonical operators.');
            return;
        }
        if (!window.confirm(`Delete ${operator.name}?`)) return;
        try {
            await axios.delete(`${API}/pigpen/${operator.operator_id}`, { withCredentials: true });
            toast.success('Operator deleted');
            fetchOperators();
        } catch (error) {
            toast.error(error.response?.data?.detail || 'Error deleting operator');
        }
    };

    const handleEdit = (operator) => {
        if (operator.is_canonical && !isSovereign) {
            toast.error('Cannot edit canonical operator. Only sovereign authority can modify canonical operators.');
            return;
        }
        setEditingOperator(operator);
        setShowForm(true);
    };

    return (
        <div className="space-y-6" data-testid="pigpen-page">
            <div className="flex items-start justify-between">
                <div>
                    <h1 className="font-mono text-3xl md:text-4xl font-bold tracking-tighter uppercase">PIG PEN</h1>
                    <p className="text-muted-foreground font-mono text-sm">Non-Human Cognition Operators Registry (TAI-D)</p>
                </div>
                {canEdit() && (
                    <button onClick={() => { setEditingOperator(null); setShowForm(true); }} className="bg-primary text-primary-foreground px-4 py-2 font-mono text-xs tracking-wider flex items-center gap-2" data-testid="add-operator-btn">
                        <Plus size={16} /> ADD OPERATOR
                    </button>
                )}
            </div>

            {/* Stats Banner */}
            <div className="bg-card border border-border p-4 flex items-center justify-between">
                <div className="flex items-center gap-6">
                    <div className="flex items-center gap-2">
                        <Shield size={16} className="text-yellow-500" />
                        <span className="font-mono text-xs text-muted-foreground">CANONICAL:</span>
                        <span className="font-mono text-sm font-bold text-yellow-400">{stats.canonical_count}</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <Bot size={16} className="text-primary" />
                        <span className="font-mono text-xs text-muted-foreground">USER-ADDED:</span>
                        <span className="font-mono text-sm font-bold">{stats.user_count}</span>
                    </div>
                </div>
                <div className="text-right">
                    <span className="font-mono text-[10px] text-muted-foreground">CANONICAL OPERATORS ARE FROZEN</span>
                </div>
            </div>

            {showForm && <OperatorForm operator={editingOperator} onSave={handleSave} onCancel={() => { setShowForm(false); setEditingOperator(null); }} />}

            <div className="flex gap-2 flex-wrap">
                <button onClick={() => setSelectedCategory('all')} className={`px-3 py-1.5 font-mono text-xs tracking-wider uppercase ${selectedCategory === 'all' ? 'bg-primary text-primary-foreground' : 'bg-secondary border border-border text-muted-foreground hover:text-foreground'}`}>
                    ALL ({operators.length})
                </button>
                {categories.map(cat => (
                    <button key={cat} onClick={() => setSelectedCategory(cat)} className={`px-3 py-1.5 font-mono text-xs tracking-wider uppercase ${selectedCategory === cat ? 'bg-primary text-primary-foreground' : 'bg-secondary border border-border text-muted-foreground hover:text-foreground'}`}>
                        {cat}
                    </button>
                ))}
            </div>

            <ScrollArea className="h-[600px]">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pr-4">
                    {loading ? (
                        <div className="col-span-2 text-center py-12 font-mono text-sm text-muted-foreground">LOADING...</div>
                    ) : operators.map(op => (
                        <OperatorCard 
                            key={op.operator_id} 
                            operator={op} 
                            onEdit={handleEdit} 
                            onDelete={handleDelete} 
                            canEdit={canEdit()} 
                            isSovereign={isSovereign}
                        />
                    ))}
                </div>
            </ScrollArea>
        </div>
    );
};

export default PigPen;
