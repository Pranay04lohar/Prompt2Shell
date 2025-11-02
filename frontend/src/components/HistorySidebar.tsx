import { useState, useEffect } from "react";
import { X, Clock, Trash2 } from "lucide-react";
import { Button } from "./ui/button";
import { ScrollArea } from "./ui/scroll-area";

interface HistorySidebarProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectPrompt: (prompt: string) => void;
}

const HistorySidebar = ({ isOpen, onClose, onSelectPrompt }: HistorySidebarProps) => {
  const [history, setHistory] = useState<string[]>([]);

  useEffect(() => {
    const stored = localStorage.getItem("prompt-history");
    if (stored) {
      try {
        setHistory(JSON.parse(stored));
      } catch (e) {
        console.error("Failed to parse history:", e);
      }
    }
  }, [isOpen]);

  const clearHistory = () => {
    localStorage.removeItem("prompt-history");
    setHistory([]);
  };

  const removeItem = (index: number) => {
    const newHistory = history.filter((_, i) => i !== index);
    setHistory(newHistory);
    localStorage.setItem("prompt-history", JSON.stringify(newHistory));
  };

  if (!isOpen) return null;

  return (
    <>
      <div 
        className="fixed inset-0 bg-background/80 backdrop-blur-sm z-40"
        onClick={onClose}
      />
      <div className="fixed left-0 top-0 h-full w-80 bg-card border-r border-border/40 z-50 animate-[slide-in-left_0.3s_ease-out]">
        <div className="flex items-center justify-between p-4 border-b border-border/40">
          <div className="flex items-center gap-2">
            <Clock className="h-5 w-5 terminal-text" />
            <h2 className="font-semibold terminal-text">Prompt History</h2>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="h-8 w-8"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        <ScrollArea className="h-[calc(100vh-8rem)]">
          <div className="p-4 space-y-2">
            {history.length === 0 ? (
              <p className="text-sm terminal-muted text-center py-8">No history yet</p>
            ) : (
              history.map((prompt, index) => (
                <div
                  key={index}
                  className="group relative p-3 rounded border border-border/40 hover:border-primary/50 transition-colors cursor-pointer"
                  onClick={() => {
                    onSelectPrompt(prompt);
                    onClose();
                  }}
                >
                  <p className="text-sm terminal-text line-clamp-3 pr-8">{prompt}</p>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="absolute top-2 right-2 h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                    onClick={(e) => {
                      e.stopPropagation();
                      removeItem(index);
                    }}
                  >
                    <Trash2 className="h-3 w-3 text-error" />
                  </Button>
                </div>
              ))
            )}
          </div>
        </ScrollArea>

        {history.length > 0 && (
          <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-border/40 bg-card">
            <Button
              variant="outline"
              size="sm"
              onClick={clearHistory}
              className="w-full border-error/40 text-error hover:bg-error/10"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Clear All History
            </Button>
          </div>
        )}
      </div>
    </>
  );
};

export default HistorySidebar;
