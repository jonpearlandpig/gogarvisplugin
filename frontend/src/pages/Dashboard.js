import { useState, useEffect } from 'react';
import axios from 'axios';
import { API, useAuth } from '@/App';
import { 
    Database, 
    FileText, 
    Layers,
    Shield,
    Link2,
    ArrowRight,
    Zap,
    Bot,
    Palette
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const StatCard = ({ icon: Icon, label, value, sublabel, onClick }) => (
    <div 
        className="bg-card border border-border p-6 hover:border-primary transition-colors duration-100 cursor-pointer group"
        onClick={onClick}
        data-testid={`stat-${label.toLowerCase().replace(/\s+/g, '-')}`}
    >
        <div className="flex items-start justify-between mb-4">
            <Icon size={20} className="text-primary" strokeWidth={1.5} />
            <ArrowRight size={16} className="text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
        </div>
        <div className="font-mono text-3xl font-bold mb-1">{value}</div>
        <div className="font-mono text-xs tracking-wider text-muted-foreground uppercase">{label}</div>
        {sublabel && (
            <div className="font-mono text-[10px] text-muted-foreground/60 mt-1">{sublabel}</div>
        )}
    </div>
);

const StatusBadge = ({ status }) => {
    const colors = {
        OPERATIONAL: 'bg-green-500',
        WARNING: 'bg-yellow-500',
        CRITICAL: 'bg-red-500',
        INACTIVE: 'bg-gray-500'
    };
    
    return (
        <span className={`inline-flex items-center gap-2 px-3 py-1 ${colors[status] || 'bg-gray-500'} text-white font-mono text-xs tracking-wider`}>
            <span className="w-1.5 h-1.5 bg-white rounded-full animate-pulse" />
            {status}
        </span>
    );
};

const ComponentRow = ({ component, onClick }) => (
    <div 
        className="flex items-center gap-4 p-4 border border-border hover:border-primary transition-colors duration-100 cursor-pointer bg-card"
        onClick={onClick}
        data-testid={`component-${component.id}`}
    >
        <div className="w-8 h-8 border border-primary flex items-center justify-center font-mono text-xs text-primary">
            {component.layer}
        </div>
        <div className="flex-1">
            <div className="font-mono text-sm font-semibold uppercase tracking-wider">{component.name}</div>
            <div className="text-xs text-muted-foreground line-clamp-1">{component.description}</div>
        </div>
        <span className="w-2 h-2 bg-green-500 rounded-full" />
    </div>
);

const Dashboard = () => {
    const navigate = useNavigate();
    const [stats, setStats] = useState(null);
    const [components, setComponents] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [statsRes, componentsRes] = await Promise.all([
                    axios.get(`${API}/dashboard/stats`),
                    axios.get(`${API}/architecture/components`)
                ]);
                setStats(statsRes.data);
                setComponents(componentsRes.data.components);
            } catch (error) {
                console.error('Error fetching dashboard data:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="font-mono text-sm text-muted-foreground animate-pulse">LOADING SYSTEM DATA...</div>
            </div>
        );
    }

    return (
        <div className="space-y-8" data-testid="dashboard-page">
            {/* Header */}
            <div className="space-y-2">
                <h1 className="font-mono text-3xl md:text-4xl font-bold tracking-tighter uppercase">
                    SYSTEM OVERVIEW
                </h1>
                <p className="text-muted-foreground font-mono text-sm">
                    Sovereign intelligence and enforcement layer status
                </p>
            </div>

            {/* System Status Banner */}
            <div className="bg-card border border-border p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                <div className="flex items-center gap-4">
                    <Shield size={24} className="text-primary" />
                    <div>
                        <div className="font-mono text-xs text-muted-foreground tracking-wider">SYSTEM STATUS</div>
                        <div className="font-mono text-lg font-bold">{stats?.system_status}</div>
                    </div>
                </div>
                <div className="flex items-center gap-4">
                    <Link2 size={24} className="text-green-500" />
                    <div>
                        <div className="font-mono text-xs text-muted-foreground tracking-wider">AUTHORITY CHAIN</div>
                        <div className="font-mono text-lg font-bold text-green-500">{stats?.authority_chain}</div>
                    </div>
                </div>
                <StatusBadge status={stats?.system_status} />
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-px bg-border">
                <StatCard 
                    icon={FileText} 
                    label="Documents" 
                    value={stats?.total_documents || 0}
                    sublabel={`${stats?.document_categories || 0} categories`}
                    onClick={() => navigate('/docs')}
                />
                <StatCard 
                    icon={Database} 
                    label="Glossary Terms" 
                    value={stats?.total_glossary_terms || 0}
                    sublabel={`${stats?.glossary_categories || 0} categories`}
                    onClick={() => navigate('/glossary')}
                />
                <StatCard 
                    icon={Layers} 
                    label="Components" 
                    value={stats?.total_components || 0}
                    sublabel={`${stats?.active_components || 0} active`}
                    onClick={() => navigate('/architecture')}
                />
                <StatCard 
                    icon={Zap} 
                    label="GARVIS AI" 
                    value="ONLINE"
                    sublabel="GPT-5.2 powered"
                    onClick={() => navigate('/chat')}
                />
            </div>

            {/* Authority Flow */}
            <div className="space-y-4">
                <div className="flex items-center justify-between">
                    <h2 className="font-mono text-xl font-bold tracking-tight uppercase">AUTHORITY FLOW</h2>
                    <button 
                        className="font-mono text-xs text-primary hover:underline tracking-wider"
                        onClick={() => navigate('/architecture')}
                        data-testid="view-architecture-btn"
                    >
                        VIEW FULL DIAGRAM →
                    </button>
                </div>
                <div className="space-y-2">
                    {components.slice(0, 4).map((component) => (
                        <ComponentRow 
                            key={component.id} 
                            component={component}
                            onClick={() => navigate('/architecture')}
                        />
                    ))}
                </div>
            </div>

            {/* Quick Actions */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <button 
                    className="bg-primary text-primary-foreground p-6 font-mono text-sm tracking-wider uppercase hover:bg-primary/90 transition-colors duration-100 flex items-center justify-between"
                    onClick={() => navigate('/chat')}
                    data-testid="quick-action-chat"
                >
                    ASK GARVIS AI
                    <ArrowRight size={18} />
                </button>
                <button 
                    className="bg-secondary text-secondary-foreground p-6 font-mono text-sm tracking-wider uppercase hover:bg-secondary/80 transition-colors duration-100 flex items-center justify-between border border-border"
                    onClick={() => navigate('/docs')}
                    data-testid="quick-action-docs"
                >
                    BROWSE DOCS
                    <ArrowRight size={18} />
                </button>
                <button 
                    className="bg-secondary text-secondary-foreground p-6 font-mono text-sm tracking-wider uppercase hover:bg-secondary/80 transition-colors duration-100 flex items-center justify-between border border-border"
                    onClick={() => navigate('/glossary')}
                    data-testid="quick-action-glossary"
                >
                    SEARCH GLOSSARY
                    <ArrowRight size={18} />
                </button>
            </div>
        </div>
    );
};

export default Dashboard;
