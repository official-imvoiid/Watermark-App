import { useState, useEffect } from 'react';

interface FontInfo {
  name: string;
  family: string;
  file: string;
}

// Convert filename to a readable font name
function fileToFontName(filename: string): string {
  // Remove extension
  const name = filename.replace(/\.(ttf|otf|woff|woff2)$/i, '');
  // Remove common suffixes like -mOBm, -MaZx, etc.
  const cleaned = name.replace(/-[a-zA-Z0-9]{3,5}$/, '');
  // Add spaces before capital letters and clean up
  return cleaned
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .replace(/([A-Z]+)([A-Z][a-z])/g, '$1 $2')
    .replace(/Demo$/i, '')
    .trim();
}

// Get font format from extension
function getFontFormat(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase();
  switch (ext) {
    case 'ttf': return 'truetype';
    case 'otf': return 'opentype';
    case 'woff': return 'woff';
    case 'woff2': return 'woff2';
    default: return 'truetype';
  }
}

export function useDynamicFonts() {
  const [fonts, setFonts] = useState<FontInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadFonts() {
      try {
        // Fetch the fonts manifest
        const response = await fetch('/fonts/fonts.json');
        if (!response.ok) {
          throw new Error('Could not load fonts.json');
        }
        
        const fontFiles: string[] = await response.json();
        
        // Create font info and load each font
        const loadedFonts: FontInfo[] = [];
        
        for (const file of fontFiles) {
          const family = fileToFontName(file);
          const format = getFontFormat(file);
          
          // Create and inject @font-face rule
          const fontFace = new FontFace(
            family,
            `url(/fonts/${file}) format('${format}')`
          );
          
          try {
            await fontFace.load();
            document.fonts.add(fontFace);
            loadedFonts.push({
              name: family,
              family: family,
              file: file
            });
          } catch (fontError) {
            console.warn(`Failed to load font: ${file}`, fontError);
          }
        }
        
        setFonts(loadedFonts);
        setLoading(false);
      } catch (err) {
        console.error('Error loading fonts:', err);
        setError(err instanceof Error ? err.message : 'Failed to load fonts');
        setLoading(false);
      }
    }
    
    loadFonts();
  }, []);

  return { fonts, loading, error };
}
