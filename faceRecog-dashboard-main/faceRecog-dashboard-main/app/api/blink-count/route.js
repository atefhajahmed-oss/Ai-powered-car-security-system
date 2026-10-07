export const dynamic = 'force-dynamic' // Ensure we get fresh data on each request

export async function GET() {
  try {
    const response = await fetch('http://localhost:5000/api/blink_count');
    if (!response.ok) {
      throw new Error('Failed to fetch blink count');
    }
    const data = await response.json();
    return Response.json(data);
  } catch (error) {
    console.error('Error fetching blink count:', error);
    return Response.json(
      { error: 'Failed to fetch blink count' },
      { status: 500 }
    );
  }
}
