import { MongoClient } from 'mongodb';

let client: MongoClient | null = null;

export async function getMongoClient(uri: string): Promise<MongoClient> {
  if (client && client.isConnected()) return client;
  client = new MongoClient(uri, { useNewUrlParser: true, useUnifiedTopology: true } as any);
  if (!client.isConnected()) await client.connect();
  return client;
}
