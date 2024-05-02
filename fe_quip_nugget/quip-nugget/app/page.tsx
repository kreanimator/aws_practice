import Image from "next/image";
import styles from "./Home.module.css";
import QuipNugget from "../components/quip_nugget";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center">
    <div>
    <QuipNugget />
    </div>
    </main>
  );
};
