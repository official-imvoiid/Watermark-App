import { ImageFile } from '@/types/watermark';
import { Button } from '@/components/ui/button';
import { ScrollArea, ScrollBar } from '@/components/ui/scroll-area';
import { ChevronLeft, ChevronRight, FolderOpen, ImagePlus, Download, Loader2 } from 'lucide-react';

interface ImageNavigationProps {
  images: ImageFile[];
  currentIndex: number;
  onNavigate: (index: number) => void;
  onLoadFolder: () => void;
  onLoadImage: () => void;
  onExport: () => void;
  isExporting?: boolean;
}

export const ImageNavigation = ({
  images,
  currentIndex,
  onNavigate,
  onLoadFolder,
  onLoadImage,
  onExport,
  isExporting = false,
}: ImageNavigationProps) => {
  const hasPrev = currentIndex > 0;
  const hasNext = currentIndex < images.length - 1;

  return (
    <div className="glass-panel rounded-lg p-3 flex flex-col gap-3 animate-fade-in">
      {/* Load Controls */}
      <div className="flex gap-2">
        <Button
          variant="secondary"
          size="sm"
          onClick={onLoadFolder}
          className="flex-1"
          disabled={isExporting}
        >
          <FolderOpen className="h-4 w-4 mr-2" />
          Folder
        </Button>
        <Button
          variant="secondary"
          size="sm"
          onClick={onLoadImage}
          className="flex-1"
          disabled={isExporting}
        >
          <ImagePlus className="h-4 w-4 mr-2" />
          Image
        </Button>
        <Button
          variant="default"
          size="sm"
          onClick={onExport}
          disabled={images.length === 0 || isExporting}
          className="flex-1 glow-accent"
        >
          {isExporting ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <Download className="h-4 w-4 mr-2" />
          )}
          {isExporting ? 'Exporting...' : 'Export ZIP'}
        </Button>
      </div>

      {/* Navigation */}
      {images.length > 0 && (
        <>
          <div className="flex items-center justify-between">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onNavigate(currentIndex - 1)}
              disabled={!hasPrev || isExporting}
              className="h-8 w-8 p-0"
            >
              <ChevronLeft className="h-5 w-5" />
            </Button>
            <span className="text-sm text-muted-foreground">
              {currentIndex + 1} / {images.length}
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onNavigate(currentIndex + 1)}
              disabled={!hasNext || isExporting}
              className="h-8 w-8 p-0"
            >
              <ChevronRight className="h-5 w-5" />
            </Button>
          </div>

          {/* Thumbnails */}
          <ScrollArea className="w-full">
            <div className="flex gap-2 pb-2">
              {images.map((image, index) => (
                <button
                  key={image.id}
                  onClick={() => onNavigate(index)}
                  disabled={isExporting}
                  className={`flex-shrink-0 w-16 h-12 rounded overflow-hidden border-2 transition-all ${
                    currentIndex === index
                      ? 'border-primary glow-accent'
                      : 'border-transparent hover:border-border'
                  } ${isExporting ? 'opacity-50' : ''}`}
                >
                  <img
                    src={image.url}
                    alt={image.name}
                    className="w-full h-full object-cover"
                  />
                </button>
              ))}
            </div>
            <ScrollBar orientation="horizontal" />
          </ScrollArea>

          <p className="text-xs text-muted-foreground text-center truncate">
            {images[currentIndex]?.name}
          </p>
        </>
      )}
    </div>
  );
};
