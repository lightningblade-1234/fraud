# AI Voice Detection API

REST API that detects whether a voice sample is **AI-generated** or **Human** across 5 languages.

## Supported Languages
- Tamil
- English  
- Hindi
- Malayalam
- Telugu

## API Endpoint

```
POST /api/voice-detection
```

### Headers
```
Content-Type: application/json
x-api-key: YOUR_SECRET_API_KEY
```

### Request Body
```json
{
  "language": "Tamil",
  "audioFormat": "mp3",
  "audioBase64": "SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU2LjM2LjEwMAAAAAAA..."
}
```

### Response
```json
{
  "status": "success",
  "language": "Tamil",
  "classification": "AI_GENERATED",
  "confidenceScore": 0.91,
  "explanation": "Unnatural pitch consistency and robotic speech patterns detected"
}
```

## Local Development

```bash
pip install -r requirements.txt
vercel dev
```

## Deployment

Deploy to Vercel:
```bash
vercel --prod
```

Set environment variable in Vercel dashboard:
- `API_KEY`: Your secret API key

## License
MIT
