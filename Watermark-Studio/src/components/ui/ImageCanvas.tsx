import { useEffect, useRef, useState, forwardRef, useImperativeHandle } from 'react';
import { Canvas as FabricCanvas, FabricText, FabricImage, FabricObject } from 'fabric';
import { WatermarkSettings } from '@/types/watermark';

interface ImageCanvasProps {
  imageUrl: string | null;
  watermarks: WatermarkSettings[];
  onWatermarkUpdate: (index: number, settings: Partial<WatermarkSettings>) => void;
  selectedWatermarkIndex: number | null;
  onSelectWatermark: (index: number | null) => void;
}

export interface ImageCanvasRef {
  getCanvas: () => FabricCanvas | null;
}

export const ImageCanvas = forwardRef<ImageCanvasRef, ImageCanvasProps>(({
  imageUrl,
  watermarks,
  onWatermarkUpdate,
  selectedWatermarkIndex,
  onSelectWatermark,
}, ref) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [fabricCanvas, setFabricCanvas] = useState<FabricCanvas | null>(null);
  const watermarkObjectsRef = useRef<Map<number, FabricObject>>(new Map());
  const backgroundImageRef = useRef<FabricImage | null>(null);
  const isUpdatingRef = useRef(false);

  useImperativeHandle(ref, () => ({
    getCanvas: () => fabricCanvas,
  }));

  // Initialize canvas
  useEffect(() => {
    if (!canvasRef.current || !containerRef.current) return;

    const container = containerRef.current;
    const canvas = new FabricCanvas(canvasRef.current, {
      width: container.clientWidth,
      height: container.clientHeight,
      backgroundColor: '#1a1a2e',
      selection: true,
      preserveObjectStacking: true,
    });

    setFabricCanvas(canvas);

    const handleResize = () => {
      canvas.setDimensions({
        width: container.clientWidth,
        height: container.clientHeight,
      });
      canvas.renderAll();
    };

    const resizeObserver = new ResizeObserver(handleResize);
    resizeObserver.observe(container);

    return () => {
      resizeObserver.disconnect();
      canvas.dispose();
    };
  }, []);

  // Handle selection events
  useEffect(() => {
    if (!fabricCanvas) return;

    const handleSelection = (e: { selected?: FabricObject[] }) => {
      if (isUpdatingRef.current) return;
      
      const selected = e.selected?.[0];
      if (selected) {
        const index = selected.get('watermarkIndex') as number | undefined;
        if (index !== undefined) {
          onSelectWatermark(index);
        }
      }
    };

    const handleDeselection = () => {
      if (isUpdatingRef.current) return;
      onSelectWatermark(null);
    };

    const handleObjectModified = (e: { target?: FabricObject }) => {
      if (isUpdatingRef.current) return;
      
      const obj = e.target;
      const index = obj?.get('watermarkIndex') as number | undefined;
      
      if (index !== undefined && obj) {
        const center = obj.getCenterPoint();
        const canvasWidth = fabricCanvas.width || 1;
        const canvasHeight = fabricCanvas.height || 1;
        
        onWatermarkUpdate(index, {
          x: (center.x / canvasWidth) * 100,
          y: (center.y / canvasHeight) * 100,
          rotation: obj.angle || 0,
          fontSize: (obj as FabricText).fontSize ? (obj as FabricText).fontSize * (obj.scaleX || 1) : undefined,
        });
      }
    };

    fabricCanvas.on('selection:created', handleSelection);
    fabricCanvas.on('selection:updated', handleSelection);
    fabricCanvas.on('selection:cleared', handleDeselection);
    fabricCanvas.on('object:modified', handleObjectModified);

    return () => {
      fabricCanvas.off('selection:created', handleSelection);
      fabricCanvas.off('selection:updated', handleSelection);
      fabricCanvas.off('selection:cleared', handleDeselection);
      fabricCanvas.off('object:modified', handleObjectModified);
    };
  }, [fabricCanvas, onSelectWatermark, onWatermarkUpdate]);

  // Load background image
  useEffect(() => {
    if (!fabricCanvas || !imageUrl) return;

    FabricImage.fromURL(imageUrl).then((img) => {
      if (backgroundImageRef.current) {
        fabricCanvas.remove(backgroundImageRef.current);
      }

      const canvasWidth = fabricCanvas.width || 800;
      const canvasHeight = fabricCanvas.height || 600;
      
      const scale = Math.min(
        (canvasWidth * 0.9) / (img.width || 1),
        (canvasHeight * 0.9) / (img.height || 1)
      );

      img.scale(scale);
      img.set({
        left: canvasWidth / 2,
        top: canvasHeight / 2,
        originX: 'center',
        originY: 'center',
        selectable: false,
        evented: false,
      });

      backgroundImageRef.current = img;
      fabricCanvas.add(img);
      fabricCanvas.sendObjectToBack(img);
      fabricCanvas.renderAll();
    });
  }, [fabricCanvas, imageUrl]);

  // Update watermarks
  useEffect(() => {
    if (!fabricCanvas) return;
    isUpdatingRef.current = true;

    const canvasWidth = fabricCanvas.width || 800;
    const canvasHeight = fabricCanvas.height || 600;

    // Remove old watermark objects
    watermarkObjectsRef.current.forEach((obj) => {
      fabricCanvas.remove(obj);
    });
    watermarkObjectsRef.current.clear();

    // Add new watermark objects
    watermarks.forEach((watermark, index) => {
      if (watermark.type === 'text') {
        const text = new FabricText(watermark.text, {
          left: (watermark.x / 100) * canvasWidth,
          top: (watermark.y / 100) * canvasHeight,
          fontFamily: watermark.fontFamily,
          fontSize: watermark.fontSize,
          fill: watermark.color,
          opacity: watermark.opacity,
          angle: watermark.rotation,
          originX: 'center',
          originY: 'center',
          textAlign: watermark.alignment,
        });

        text.set('watermarkIndex', index);
        watermarkObjectsRef.current.set(index, text);
        fabricCanvas.add(text);

        if (selectedWatermarkIndex === index) {
          fabricCanvas.setActiveObject(text);
        }
      } else if (watermark.type === 'image' && watermark.imageUrl) {
        FabricImage.fromURL(watermark.imageUrl).then((img) => {
          img.set({
            left: (watermark.x / 100) * canvasWidth,
            top: (watermark.y / 100) * canvasHeight,
            opacity: watermark.opacity,
            angle: watermark.rotation,
            originX: 'center',
            originY: 'center',
            scaleX: watermark.fontSize / 100,
            scaleY: watermark.fontSize / 100,
          });

          img.set('watermarkIndex', index);
          watermarkObjectsRef.current.set(index, img);
          fabricCanvas.add(img);
          fabricCanvas.bringObjectToFront(img);

          if (selectedWatermarkIndex === index) {
            fabricCanvas.setActiveObject(img);
          }
          
          fabricCanvas.renderAll();
        });
      }
    });

    fabricCanvas.renderAll();
    
    setTimeout(() => {
      isUpdatingRef.current = false;
    }, 50);
  }, [fabricCanvas, watermarks, selectedWatermarkIndex]);

  return (
    <div 
      ref={containerRef} 
      className="flex-1 relative overflow-hidden rounded-lg border border-border bg-muted/20"
    >
      <canvas ref={canvasRef} className="block" />
      {!imageUrl && (
        <div className="absolute inset-0 flex items-center justify-center text-muted-foreground">
          <p className="text-lg">Load an image to start editing</p>
        </div>
      )}
    </div>
  );
});

ImageCanvas.displayName = 'ImageCanvas';
