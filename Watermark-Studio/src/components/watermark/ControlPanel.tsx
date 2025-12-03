import { WatermarkSettings, FontInfo, SYSTEM_FONTS } from '@/types/watermark';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Type, 
  Image, 
  RotateCw,
  Trash2,
  Copy,
  Sparkles,
  Loader2
} from 'lucide-react';

interface ControlPanelProps {
  watermarks: WatermarkSettings[];
  selectedIndex: number | null;
  onUpdate: (index: number, settings: Partial<WatermarkSettings>) => void;
  onAdd: (type: 'text' | 'image') => void;
  onDelete: (index: number) => void;
  onSelect: (index: number) => void;
  onBatchCopy: () => void;
  onLoadWatermarkImage: () => void;
  customFonts: FontInfo[];
  fontsLoading: boolean;
}

export const ControlPanel = ({
  watermarks,
  selectedIndex,
  onUpdate,
  onAdd,
  onDelete,
  onSelect,
  onBatchCopy,
  onLoadWatermarkImage,
  customFonts,
  fontsLoading,
}: ControlPanelProps) => {
  const selectedWatermark = selectedIndex !== null ? watermarks[selectedIndex] : null;

  const isCustomFont = (fontFamily: string) => {
    return customFonts.some(f => f.family === fontFamily);
  };

  return (
    <div className="w-80 glass-panel rounded-lg p-4 flex flex-col gap-4 animate-slide-in">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-foreground">Watermarks</h2>
        <div className="flex gap-1">
          <Button
            size="sm"
            variant="ghost"
            onClick={() => onAdd('text')}
            className="h-8 w-8 p-0"
            title="Add text watermark"
          >
            <Type className="h-4 w-4" />
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => onAdd('image')}
            className="h-8 w-8 p-0"
            title="Add image watermark"
          >
            <Image className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Watermark List */}
      <ScrollArea className="h-32 rounded border border-border/50 bg-muted/30">
        <div className="p-2 space-y-1">
          {watermarks.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-4">
              No watermarks added
            </p>
          ) : (
            watermarks.map((wm, index) => (
              <button
                key={index}
                onClick={() => onSelect(index)}
                className={`w-full flex items-center gap-2 p-2 rounded text-left text-sm transition-colors ${
                  selectedIndex === index 
                    ? 'bg-primary/20 text-primary border border-primary/30' 
                    : 'hover:bg-muted/50 text-foreground'
                }`}
              >
                {wm.type === 'text' ? (
                  <Type className="h-3 w-3 flex-shrink-0" />
                ) : (
                  <Image className="h-3 w-3 flex-shrink-0" />
                )}
                <span className="truncate flex-1">
                  {wm.type === 'text' ? wm.text : wm.imageName || 'Image'}
                </span>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(index);
                  }}
                  className="h-6 w-6 p-0 opacity-50 hover:opacity-100"
                >
                  <Trash2 className="h-3 w-3" />
                </Button>
              </button>
            ))
          )}
        </div>
      </ScrollArea>

      {/* Batch Copy Button */}
      <Button
        variant="secondary"
        size="sm"
        onClick={onBatchCopy}
        disabled={watermarks.length === 0}
        className="w-full"
      >
        <Copy className="h-4 w-4 mr-2" />
        Copy to All Images
      </Button>

      {/* Watermark Settings */}
      {selectedWatermark && selectedIndex !== null && (
        <div className="space-y-4 pt-4 border-t border-border/50">
          <h3 className="text-sm font-medium text-muted-foreground">Settings</h3>

          {selectedWatermark.type === 'text' ? (
            <>
              {/* Text Input */}
              <div className="space-y-2">
                <Label className="text-xs">Text</Label>
                <Input
                  value={selectedWatermark.text}
                  onChange={(e) => onUpdate(selectedIndex, { text: e.target.value })}
                  className="h-8 text-sm bg-muted/30"
                />
              </div>

              {/* Font Selection */}
              <div className="space-y-2">
                <Label className="text-xs flex items-center gap-1">
                  Font
                  {selectedWatermark.fontFamily && isCustomFont(selectedWatermark.fontFamily) && (
                    <Sparkles className="h-3 w-3 text-primary" />
                  )}
                  {fontsLoading && <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />}
                </Label>
                <ScrollArea className="h-32 rounded border border-border/50 bg-muted/30">
                  <div className="p-1 space-y-1">
                    {/* Custom Fonts Section */}
                    {customFonts.length > 0 && (
                      <>
                        <div className="px-2 py-1 text-xs text-primary font-medium flex items-center gap-1">
                          <Sparkles className="h-3 w-3" />
                          Custom Fonts ({customFonts.length})
                        </div>
                        {customFonts.map((font) => (
                          <button
                            key={font.family}
                            onClick={() => onUpdate(selectedIndex, { fontFamily: font.family })}
                            className={`w-full text-left px-2 py-1.5 rounded text-sm transition-colors ${
                              selectedWatermark.fontFamily === font.family
                                ? 'bg-primary/20 text-primary'
                                : 'hover:bg-muted/50'
                            }`}
                            style={{ fontFamily: font.family }}
                          >
                            {font.name}
                          </button>
                        ))}
                      </>
                    )}
                    
                    {/* System Fonts Section */}
                    <div className="px-2 py-1 mt-2 text-xs text-muted-foreground font-medium border-t border-border/30 pt-2">
                      System Fonts
                    </div>
                    {SYSTEM_FONTS.map((font) => (
                      <button
                        key={font.family}
                        onClick={() => onUpdate(selectedIndex, { fontFamily: font.family })}
                        className={`w-full text-left px-2 py-1.5 rounded text-sm transition-colors ${
                          selectedWatermark.fontFamily === font.family
                            ? 'bg-primary/20 text-primary'
                            : 'hover:bg-muted/50'
                        }`}
                        style={{ fontFamily: font.family }}
                      >
                        {font.name}
                      </button>
                    ))}
                  </div>
                </ScrollArea>
              </div>

              {/* Font Size */}
              <div className="space-y-2">
                <Label className="text-xs">Size: {selectedWatermark.fontSize}px</Label>
                <Slider
                  value={[selectedWatermark.fontSize]}
                  onValueChange={([v]) => onUpdate(selectedIndex, { fontSize: v })}
                  min={8}
                  max={200}
                  step={1}
                  className="py-2"
                />
              </div>

            </>
          ) : (
            <>
              {/* Image Watermark Settings */}
              <Button
                variant="secondary"
                size="sm"
                onClick={onLoadWatermarkImage}
                className="w-full"
              >
                <Image className="h-4 w-4 mr-2" />
                Select Image
              </Button>

              {selectedWatermark.imageName && (
                <p className="text-xs text-muted-foreground truncate">
                  {selectedWatermark.imageName}
                </p>
              )}

              {/* Image Size */}
              <div className="space-y-2">
                <Label className="text-xs">Scale: {selectedWatermark.fontSize}%</Label>
                <Slider
                  value={[selectedWatermark.fontSize]}
                  onValueChange={([v]) => onUpdate(selectedIndex, { fontSize: v })}
                  min={10}
                  max={200}
                  step={1}
                  className="py-2"
                />
              </div>
            </>
          )}

          {/* Color - Only for text watermarks */}
          {selectedWatermark.type === 'text' && (
            <div className="space-y-2">
              <Label className="text-xs">Color</Label>
              <div className="flex gap-2 items-center">
                <input
                  type="color"
                  value={selectedWatermark.color}
                  onChange={(e) => onUpdate(selectedIndex, { color: e.target.value })}
                  className="w-10 h-8 rounded cursor-pointer border border-border"
                />
                <Input
                  value={selectedWatermark.color}
                  onChange={(e) => onUpdate(selectedIndex, { color: e.target.value })}
                  className="h-8 text-sm bg-muted/30 flex-1 font-mono"
                />
              </div>
            </div>
          )}

          {/* Opacity */}
          <div className="space-y-2">
            <Label className="text-xs">Opacity: {Math.round(selectedWatermark.opacity * 100)}%</Label>
            <Slider
              value={[selectedWatermark.opacity * 100]}
              onValueChange={([v]) => onUpdate(selectedIndex, { opacity: v / 100 })}
              min={0}
              max={100}
              step={1}
              className="py-2"
            />
          </div>

          {/* Rotation */}
          <div className="space-y-2">
            <Label className="text-xs flex items-center gap-2">
              <RotateCw className="h-3 w-3" />
              Rotation: {selectedWatermark.rotation}°
            </Label>
            <Slider
              value={[selectedWatermark.rotation]}
              onValueChange={([v]) => onUpdate(selectedIndex, { rotation: v })}
              min={-180}
              max={180}
              step={1}
              className="py-2"
            />
          </div>
        </div>
      )}
    </div>
  );
};
