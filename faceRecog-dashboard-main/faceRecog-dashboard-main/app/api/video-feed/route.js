export const dynamic = 'force-dynamic' // Ensure we get fresh data on each request

export async function GET() {
  try {
    const response = await fetch('http://localhost:5000/api/video_feed');
    if (!response.ok) {
      throw new Error('Failed to fetch video feed');
    }
    
    // Get the readable stream from the response
    const stream = response.body;
    
    // Create a new response with the same stream
    return new Response(stream, {
      status: 200,
      headers: {
        'Content-Type': response.headers.get('Content-Type'),
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });
  } catch (error) {
    console.error('Error fetching video feed:', error);
    return new Response(JSON.stringify({ error: 'Failed to fetch video feed' }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }
}
