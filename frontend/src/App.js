import { useState, useEffect, createContext, useContext } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, NavLink, useLocation, useNavigate } from "react-router-dom";
import axios from "axios";
import { 
    LayoutDashboard, 
    FileText, 
    Network, 
    MessageSquare, 
    BookOpen,
    Settings,
    Sun,
    Moon,
    ChevronRight,
    Menu,
    X,
    Users,
    History,
    Bot,
    Palette,
    LogOut,
    LogIn
} from "lucide-react";
import { Toaster, toast } from "sonner";

import Dashboard from "@/pages/Dashboard";
import Documentation from "@/pages/Documentation";
import Architecture from "@/pages/Architecture";
import GarvisChat from "@/pages/GarvisChat";
import Glossary from "@/pages/Glossary";
import SettingsPage from "@/pages/Settings";
import PigPen from "@/pages/PigPen";
import Brands from "@/pages/Brands";
import AuditLog from "@/pages/AuditLog";
import AdminUsers from "@/pages/AdminUsers";
import Login from "@/pages/Login";
import AuthCallback from "@/pages/AuthCallback";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext();

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) throw new Error("useAuth must be used within AuthProvider");
    return context;
};

const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        checkAuth();
    }, []);

    const checkAuth = async () => {
        try {
            const response = await axios.get(`${API}/auth/me`, { withCredentials: true });
            setUser(response.data);
        } catch (error) {
            setUser(null);
        } finally {
            setLoading(false);
        }
    };

    const login = (userData) => {
        setUser(userData);
    };

    const logout = async () => {
        try {
            await axios.post(`${API}/auth/logout`, {}, { withCredentials: true });
        } catch (error) {
            console.error("Logout error:", error);
        }
        setUser(null);
    };

    const canEdit = () => user?.role === "admin" || user?.role === "editor";
    const isAdmin = () => user?.role === "admin";

    return (
        <AuthContext.Provider value={{ user, loading, login, logout, checkAuth, canEdit, isAdmin }}>
            {children}
        </AuthContext.Provider>
    );
};

// Theme Context
const ThemeContext = createContext();

export const useTheme = () => {
    const context = useContext(ThemeContext);
    if (!context) throw new Error("useTheme must be used within ThemeProvider");
    return context;
};

const ThemeProvider = ({ children }) => {
    const [theme, setTheme] = useState(() => {
        const saved = localStorage.getItem("gogarvis-theme");
        return saved || "dark";
    });

    useEffect(() => {
        localStorage.setItem("gogarvis-theme", theme);
        document.documentElement.classList.remove("light", "dark");
        if (theme === "light") {
            document.documentElement.classList.add("light");
        }
    }, [theme]);

    const toggleTheme = () => setTheme(theme === "dark" ? "light" : "dark");

    return (
        <ThemeContext.Provider value={{ theme, toggleTheme }}>
            {children}
        </ThemeContext.Provider>
    );
};

// Navigation items
const getNavItems = (user) => {
    const items = [
        { path: "/", icon: LayoutDashboard, label: "DASHBOARD" },
        { path: "/docs", icon: FileText, label: "DOCUMENTATION" },
        { path: "/architecture", icon: Network, label: "ARCHITECTURE" },
        { path: "/pigpen", icon: Bot, label: "PIG PEN" },
        { path: "/brands", icon: Palette, label: "BRANDS" },
        { path: "/chat", icon: MessageSquare, label: "GARVIS AI" },
        { path: "/glossary", icon: BookOpen, label: "GLOSSARY" },
    ];

    if (user) {
        items.push({ path: "/audit", icon: History, label: "AUDIT LOG" });
        if (user.role === "admin") {
            items.push({ path: "/admin/users", icon: Users, label: "USERS" });
        }
    }

    items.push({ path: "/settings", icon: Settings, label: "SETTINGS" });

    return items;
};

// Sidebar Component
const Sidebar = ({ isOpen, onClose }) => {
    const location = useLocation();
    const navigate = useNavigate();
    const { theme, toggleTheme } = useTheme();
    const { user, logout } = useAuth();
    const navItems = getNavItems(user);

    const handleLogout = async () => {
        await logout();
        navigate("/");
        toast.success("Logged out successfully");
    };

    return (
        <>
            {isOpen && (
                <div 
                    className="fixed inset-0 bg-black/50 z-40 lg:hidden"
                    onClick={onClose}
                    data-testid="sidebar-overlay"
                />
            )}
            
            <aside 
                className={`
                    fixed top-0 left-0 h-full w-64 bg-background border-r border-border z-50
                    transform transition-transform duration-200 ease-linear
                    ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
                `}
                data-testid="sidebar"
            >
                <div className="h-16 border-b border-border flex items-center px-6">
                    <span className="font-mono text-xl font-bold tracking-tight text-primary">
                        GOGARVIS
                    </span>
                    <button 
                        className="ml-auto lg:hidden p-2 hover:bg-secondary"
                        onClick={onClose}
                        data-testid="sidebar-close-btn"
                    >
                        <X size={18} />
                    </button>
                </div>

                <nav className="p-4 space-y-1 h-[calc(100%-16rem)] overflow-y-auto">
                    {navItems.map((item) => {
                        const Icon = item.icon;
                        const isActive = location.pathname === item.path;
                        
                        return (
                            <NavLink
                                key={item.path}
                                to={item.path}
                                onClick={onClose}
                                className={`
                                    flex items-center gap-3 px-4 py-3 font-mono text-xs tracking-wider
                                    transition-colors duration-100
                                    ${isActive 
                                        ? 'bg-primary text-primary-foreground' 
                                        : 'text-muted-foreground hover:bg-secondary hover:text-foreground'
                                    }
                                `}
                                data-testid={`nav-${item.label.toLowerCase().replace(/\s+/g, '-')}`}
                            >
                                <Icon size={16} strokeWidth={1.5} />
                                {item.label}
                                {isActive && <ChevronRight size={14} className="ml-auto" />}
                            </NavLink>
                        );
                    })}
                </nav>

                <div className="absolute bottom-0 left-0 right-0 border-t border-border">
                    {user ? (
                        <div className="p-4 border-b border-border">
                            <div className="flex items-center gap-3 mb-3">
                                {user.picture ? (
                                    <img src={user.picture} alt={user.name} className="w-8 h-8 rounded-full" />
                                ) : (
                                    <div className="w-8 h-8 bg-primary flex items-center justify-center font-mono text-xs text-primary-foreground">
                                        {user.name?.charAt(0).toUpperCase()}
                                    </div>
                                )}
                                <div className="flex-1 min-w-0">
                                    <div className="font-mono text-xs truncate">{user.name}</div>
                                    <div className="font-mono text-[10px] text-primary uppercase">{user.role}</div>
                                </div>
                            </div>
                            <button
                                onClick={handleLogout}
                                className="w-full flex items-center gap-3 px-4 py-2 font-mono text-xs tracking-wider text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors"
                                data-testid="logout-btn"
                            >
                                <LogOut size={14} />
                                LOGOUT
                            </button>
                        </div>
                    ) : (
                        <div className="p-4 border-b border-border">
                            <NavLink
                                to="/login"
                                className="w-full flex items-center gap-3 px-4 py-2 font-mono text-xs tracking-wider bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
                                data-testid="login-btn"
                            >
                                <LogIn size={14} />
                                LOGIN
                            </NavLink>
                        </div>
                    )}
                    <div className="p-4">
                        <button
                            onClick={toggleTheme}
                            className="w-full flex items-center gap-3 px-4 py-2 font-mono text-xs tracking-wider text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors"
                            data-testid="theme-toggle-btn"
                        >
                            {theme === "dark" ? <Sun size={14} /> : <Moon size={14} />}
                            {theme === "dark" ? "LIGHT MODE" : "DARK MODE"}
                        </button>
                        <div className="px-4 py-2">
                            <span className="font-mono text-[10px] text-muted-foreground tracking-wider">
                                v2.0.0 // PEARL & PIG
                            </span>
                        </div>
                    </div>
                </div>
            </aside>
        </>
    );
};

// Header Component
const Header = ({ onMenuClick }) => {
    const location = useLocation();
    const { user } = useAuth();
    const navItems = getNavItems(user);
    const currentPage = navItems.find(item => item.path === location.pathname);

    return (
        <header className="h-16 border-b border-border flex items-center px-6 bg-background/80 backdrop-blur-sm sticky top-0 z-30">
            <button 
                className="lg:hidden p-2 mr-4 hover:bg-secondary"
                onClick={onMenuClick}
                data-testid="menu-toggle-btn"
            >
                <Menu size={20} />
            </button>
            <div className="flex items-center gap-2">
                <span className="font-mono text-xs text-muted-foreground tracking-wider">
                    GOGARVIS //
                </span>
                <span className="font-mono text-sm font-semibold tracking-wider uppercase">
                    {currentPage?.label || "SYSTEM"}
                </span>
            </div>
            <div className="ml-auto flex items-center gap-2">
                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                <span className="font-mono text-xs text-muted-foreground tracking-wider">
                    OPERATIONAL
                </span>
            </div>
        </header>
    );
};

// Layout Component
const Layout = ({ children }) => {
    const [sidebarOpen, setSidebarOpen] = useState(false);

    return (
        <div className="min-h-screen bg-background">
            <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
            <div className="lg:ml-64">
                <Header onMenuClick={() => setSidebarOpen(true)} />
                <main className="p-6 md:p-8 lg:p-12">
                    {children}
                </main>
            </div>
        </div>
    );
};

// App Router with Auth Callback Detection
function AppRouter() {
    const location = useLocation();
    
    // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    // Check for session_id in URL fragment SYNCHRONOUSLY during render
    if (location.hash?.includes('session_id=')) {
        return <AuthCallback />;
    }

    return (
        <Layout>
            <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/docs" element={<Documentation />} />
                <Route path="/architecture" element={<Architecture />} />
                <Route path="/pigpen" element={<PigPen />} />
                <Route path="/brands" element={<Brands />} />
                <Route path="/chat" element={<GarvisChat />} />
                <Route path="/glossary" element={<Glossary />} />
                <Route path="/audit" element={<AuditLog />} />
                <Route path="/admin/users" element={<AdminUsers />} />
                <Route path="/settings" element={<SettingsPage />} />
                <Route path="/login" element={<Login />} />
            </Routes>
        </Layout>
    );
}

function App() {
    return (
        <ThemeProvider>
            <AuthProvider>
                <div className="App">
                    <BrowserRouter>
                        <AppRouter />
                    </BrowserRouter>
                    <Toaster position="bottom-right" theme="dark" />
                </div>
            </AuthProvider>
        </ThemeProvider>
    );
}

export default App;
