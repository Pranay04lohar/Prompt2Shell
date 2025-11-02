import { Terminal } from "lucide-react";
import { Badge } from "./ui/badge";
import { useNavigate } from "react-router-dom";

interface HeaderProps {
  modelName?: string;
  apiStatus?: "connected" | "disconnected" | "loading";
}

const Header = ({ modelName = " Phi-3-mini (QLoRA Fine-Tuned)", apiStatus = "connected" }: HeaderProps) => {
  const navigate = useNavigate();
  
  const statusColors = {
    connected: "bg-success",
    disconnected: "bg-error",
    loading: "bg-warning",
  };

  const handleHomeClick = () => {
    navigate("/");
    window.location.reload();
  };

  return (
    <header className="border-b border-border/40 bg-card/30 backdrop-blur-sm">
      <div className="container mx-auto px-4 py-3 flex items-center justify-between">
        <button 
          onClick={handleHomeClick}
          className="flex items-center gap-3 hover:opacity-80 transition-opacity cursor-pointer"
          aria-label="Go to homepage"
        >
          <Terminal className="w-6 h-6 terminal-text terminal-glow" />
          <h1 className="text-xl font-bold terminal-text">Prompt2Shell</h1>
        </button>
        
        <div className="flex items-center gap-3">
          <Badge variant="outline" className="terminal-text border-border/60 text-xs hidden sm:inline-flex">
            {modelName}
          </Badge>
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${statusColors[apiStatus]} animate-pulse`} />
            <span className="text-xs terminal-muted hidden sm:inline">
              {apiStatus === "connected" ? "Connected" : apiStatus === "loading" ? "Connecting..." : "Disconnected"}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
