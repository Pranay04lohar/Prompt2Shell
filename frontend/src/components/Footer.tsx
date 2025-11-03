import { Github } from "lucide-react";

const Footer = () => {
  return (
    <footer className="border-t border-border/40 bg-card/30 backdrop-blur-sm mt-auto">
      <div className="container mx-auto px-4 py-4">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-2 text-xs terminal-muted">
          <div className="flex items-center gap-2">
            <span>Built with</span>
            <span className="terminal-accent font-semibold"> Phi-3-mini (QLoRA Fine-Tuned)</span>
            <span>•</span>
            <span className="terminal-text">Prompt2Shell</span>
          </div>
          
          <a
            href="https://github.com/Pranay04lohar/Prompt2Shell"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 hover:terminal-text transition-colors"
            aria-label="View on GitHub"
          >
            <Github className="h-4 w-4" />
            <span className="hidden sm:inline">View on GitHub</span>
          </a>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
