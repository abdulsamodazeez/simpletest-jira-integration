import catalogJson from "@/data/catalog.json";

export type CatalogParam = {
  name: string;
  description: string;
  required: boolean;
  placement: string;
  default: string | null;
};

export type CatalogObject = {
  name: string;
  description: string;
  endpoint: string;
  api: string;
  response_path: string | null;
  notes: string;
  cloud_supported: boolean;
  params: CatalogParam[];
};

export const CATALOG: CatalogObject[] = catalogJson as CatalogObject[];

export function catalogByName(): Map<string, CatalogObject> {
  return new Map(CATALOG.map((o) => [o.name, o]));
}
